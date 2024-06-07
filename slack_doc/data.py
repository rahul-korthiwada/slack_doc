import requests
from base64 import b64encode
from dotenv import load_dotenv
import os
import argparse
import multiprocessing as mp
import pandas as pd
import re
from slack_scraper import scrape_data_from_slack
from tqdm import tqdm
import sys
from slack_sdk import WebClient
from chatai import LLM
import json
from glob import glob

class JiraScraper:
	def __init__(self,jira_domain) -> None:
		self.user_name = os.getenv("JIRA_USERNAME")
		self.token = os.getenv("JIRA_TOKEN")
		self.credentials = "Basic " + \
		b64encode((self.user_name + ":" + self.token).encode("ascii")).decode("ascii")
		self.headers = {
		"Accept": "application/json",
		"Authorization": self.credentials
		}
		self.jira_domain = jira_domain


	def fetch_child_epic_ids(self,parent_epic):
		url = "https://" + self.jira_domain + "/rest/api/2/search/"
		params = {
			"jql": "parent = " + parent_epic,
			"maxResults": 100,
			"fields": "key",
			"startAt": 0
		}
		response = requests.get(url, headers=self.headers,params=params)
		epic_ids = []
		if response.status_code == 200:
			data = response.json()
			total_issues = data['total']

			while params['startAt'] < total_issues:
				try:
					# Send request for the current page
					response = requests.get(url, params=params, headers=self.headers)
					if response.status_code == 200:
						data = response.json()
						epic_ids += [issue["key"] for issue in data['issues']]

						# Move to the next page
						params['startAt'] += len(data["issues"])
					else:
						print("Error:", response.status_code, response.text)
				except Exception as ex:
					print(f"exception :: {ex} in data : {data}")
					continue
		else:
			print("Error:", response.status_code, response.text)
		return epic_ids

	def fetch_data(self,epic_id):
		df = pd.DataFrame(columns=["channel_id","thread_ts","thread_data","merchant_id","errors","slack_url","jira_labels",
								"jira_category","llm_category","exact_error","thread_meta_data","llm_summary","jira_rca",
								"jira_description","jira_title","jira_epic"])
		url = "https://" + self.jira_domain + "/rest/api/latest/issue/" + epic_id
		slack_url_field = "customfield_10290"
		rca_field = "customfield_10344"
		category_field = "customfield_10454" # customfield_10454.value
		params = {
		"fields": f"{slack_url_field},{rca_field},{category_field},labels,description,summary"
		}

		response = requests.get(url,headers=self.headers,params=params)
		data = response.json()["fields"]
		fields = data.keys()
		df.loc[0,"jira_epic"] = epic_id
		slack_urls = []
		if slack_url_field not in fields:
			if data["description"]:
				pattern = r"https://[\w.-]+\.slack\.com/archives/[\w-]+/[\w-]+"
				slack_urls += list(set(re.findall(pattern,data["description"])))
		else:
			slack_urls = slack_urls.append(data[slack_url_field]) if data[slack_url_field] else []
		df.loc[0,"slack_url"] = slack_urls
		df.loc[0,"jira_labels"] = data["labels"]
		if rca_field in fields:
			df.loc[0,"jira_rca"] = data[rca_field] if data[rca_field] else None
		if category_field in fields:
			df.loc[0,"jira_category"] = data[category_field]["value"] if data[category_field] is not None else None
		df.loc[0,"jira_title"] = data["summary"]
		df.loc[0,"jira_description"] = data["description"]

		# fetch using slack url
		thread_data = []
		if slack_urls is not None:
			for slack_url in slack_urls:
				channel_id = slack_url.split("/")[4]
				ts = str(int(slack_url.split("/")[5][1:])/1000000)
				thread_data.append(scrape_data_from_slack(channel_id,ts))
		df.loc[0,"thread_data"] = thread_data
		return df

	def fetch(self,epic):
		child_epic_ids = self.fetch_child_epic_ids(epic)
		num_workers = mp.cpu_count()
		with mp.Pool(num_workers) as pool:
			results = list(tqdm(
				pool.imap(self.fetch_data, child_epic_ids),
				total=len(child_epic_ids),
				desc='Fetching JIRA Issues'))
		final_df = pd.concat(results,ignore_index=True)
		final_df.to_csv("data.csv",index=False)


class SlackScraper:
	def __init__(self,slack_domain,channel_id=None,start_thread_ts=None,jira_file_path=None) -> None:
		self.thread_ts = []
		self.client = WebClient(token=os.getenv("SLACK_API_TOKEN"))
		self.channel_id = channel_id if channel_id else os.getenv("SLACK_CHANNEL_ID")
		self.slack_domain = slack_domain if slack_domain else os.getenv("SLACK_DOMAIN")
		self.start_thread_ts = start_thread_ts if start_thread_ts else 1641044087 # from January 1st 2022
		self.jira_file_path = jira_file_path if jira_file_path else os.getcwd() + "/data.csv"
		self.df = pd.read_csv(self.jira_file_path,index_col=False,dtype=str)

	def fetch_slack_thread_ids(self,cursor=None):
		response = self.client.conversations_history(
			channel=self.channel_id,
			oldest=self.start_thread_ts,
			inclusive=True,
			limit=200,
			cursor=cursor)
		res_metadata = response['response_metadata']
		next_cursor = res_metadata['next_cursor'] if res_metadata is not None else None
		for d in response["messages"]:
			keys = d.keys()
			# filter out bot threads without replies
			if not ("bot_id" in keys and "reply_count" not in keys):
				self.thread_ts.append(d["ts"])

		if next_cursor is not None:
			self.fetch_slack_thread_ids(next_cursor)
		return self.thread_ts

	def fetch_jira_epics(self,data):
		jira_url_pattern = r"https://[\w.-]+\.atlassian\.net/browse/[\w-]+"
		jira_urls = []
		if data["data"]:
			for obj in data["data"]:
				urls = re.findall(jira_url_pattern,obj["message"])
				jira_urls += urls
		if data["additional_data"]:
			for obj in data["additional_data"]:
				add_urls = re.findall(jira_url_pattern,obj["message"])
				jira_urls += add_urls
		epics = [os.path.split(x)[1] for x in jira_urls]
		return epics

	def get_model_results(self,ts):
		azure = LLM()
		slack_data_path = "docs_v5/"+ ts + ".md"
		json_path = "responses_v5/" + ts + ".json"
		try:
			ts_new = ts.replace(".","")
			slack_url = f"https://{self.slack_domain}/archives/{self.channel_id}/p{ts_new}"

			if os.path.exists(slack_data_path):
				with open(slack_data_path,"r") as f:
					parsed_data = json.load(f)
			else:
				parsed_data = scrape_data_from_slack(self.channel_id,ts)
				with open(slack_data_path,"w") as fp:
					fp.write(json.dumps(parsed_data))

			if os.path.exists(json_path):
				return None
			else:
				res = azure.post_request_to_model(parsed_data)
				json_res = azure.to_json(res)
				epics = self.fetch_jira_epics(parsed_data)
				json_res["channel_id"] = self.channel_id
				json_res["thread_ts"] = "p" + ts
				json_res["thread_data"] = parsed_data
				json_res["slack_url"] = slack_url
				json_res["epics"] = epics
				with open(json_path,"w") as f:
					f.write(json.dumps(json_res))
		except Exception as ex:
			print(f"exception {ex} in {ts}")
			return None
		return None

	def flatten_list(self,data):
		keys_to_flatten = [k for k in data.keys() if k != "thread_data"]
		for key in keys_to_flatten:
			if isinstance(data[key],list):
				if all(isinstance(v,str) for v in data[key]):
					data[key] = ",".join(data[key])
				else:
					data[key] = ""
		return data

	def merge_slack_jira_data(self):
		jira_df = pd.read_csv("./data.csv",index_col=False,dtype=str)
		file_paths = glob("responses_v5/*.json")
		for idx,path in tqdm(enumerate(file_paths),total=len(file_paths)):
			with open(path,"r") as fp:
				slack_data = json.load(fp)
			if slack_data["epics"]:
				for i,epic in enumerate(slack_data["epics"]):
					if epic in list(jira_df["jira_epic"].values):
							slack_data["jira_epic"] = epic
							out = self.flatten_list(slack_data)
							jira_df.loc[jira_df["jira_epic"] == epic, out.keys()] = out.values()
					else:
						idx = len(self.df)
						self.df.loc[idx,out.keys()] = out.values()
			else:
				slack_data.pop('epics')
				slack_data['jira_epic'] = None
				jira_df.loc[len(jira_df)] = slack_data
		jira_df.to_csv("combined_data.csv",index=False)

def main():
	parser = argparse.ArgumentParser()
	num_workers = mp.cpu_count()

	# Add arguments
	parser.add_argument("--env-path", help="ENV file path", required=True)
	parser.add_argument("--jira-epic", help="JIRA Epic Id", default=None)
	parser.add_argument("--jira-domain", help="JIRA domain", default=None)
	parser.add_argument("--slack-domain", help="slack domain", default=None)
	args = parser.parse_args()
	env_file_path = args.env_path
	load_dotenv(env_file_path,override=True)

	if not args.jira_epic:
		slack = SlackScraper(args.slack_domain)
		print("Fetching slack thread ids ...")
		slack.fetch_slack_thread_ids()
		print("Done fetching slack thread ids")
		with mp.Pool(num_workers) as pool:
			results = list(tqdm(
				pool.imap(slack.get_model_results, slack.thread_ts),
				total=len(slack.thread_ts),
				desc='Fetching Model Responses'))
		print("Done writing files")
		slack.merge_slack_jira_data()
	else:
		jira = JiraScraper(args.jira_domain)
		jira.fetch(args.jira_epic)


if __name__ == "__main__":
	main()