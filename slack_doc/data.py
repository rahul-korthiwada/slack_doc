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
import ast

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

def create_dir_if_missing(path):
    if not os.path.exists(path):
        print(f"{path} not present, creating it")
        os.makedirs(path)

class SlackScraper:
    def __init__(self,slack_domain,channel_ids=None,start_thread_ts=None,jira_file_path=None) -> None:
        self.client = WebClient(token=os.getenv("SLACK_API_TOKEN"))
        self.slack_domain = slack_domain if slack_domain else os.getenv("SLACK_DOMAIN")
        self.start_thread_ts = start_thread_ts if start_thread_ts else 1641044087 # from January 1st 2022

    def fetch_slack_thread_ids(self,channel_id,thread_ts,cursor=None):
        ts = []
        response = self.client.conversations_history(
            channel=channel_id,
            oldest=self.start_thread_ts,
            inclusive=True,
            limit=200,
            cursor=cursor)
        res_metadata = response['response_metadata']
        next_cursor = res_metadata['next_cursor'] if res_metadata is not None else None
        for idx,d in enumerate(response["messages"]):
            keys = d.keys()
            # filter out bot threads without replies
            if not ("bot_id" in keys and "reply_count" not in keys):
                thread_ts.append((d["ts"],channel_id))

        if next_cursor is not None:
            ts = self.fetch_slack_thread_ids(channel_id,thread_ts,next_cursor)
        return (thread_ts + ts)

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

    def get_model_results(self,thread_ts):
        azure = LLM()
        ts,channel_id = thread_ts
        slack_data_path = f"{os.getcwd()}/docs_v5/{channel_id}/{ts}.md"
        json_path = f"{os.getcwd()}/responses_v5/{channel_id}/{ts}.json"
        try:
            ts_new = ts.replace(".","")
            slack_url = f"https://{self.slack_domain}/archives/{channel_id}/p{ts_new}"

            if os.path.exists(slack_data_path):
                with open(slack_data_path,"r") as f:
                    parsed_data = json.load(f)
            else:
                parsed_data = scrape_data_from_slack(channel_id,ts)
                with open(slack_data_path,"w") as fp:
                    fp.write(json.dumps(parsed_data))

            if os.path.exists(json_path):
                return None
            else:
                res = azure.post_request_to_model(parsed_data)
                json_res = azure.to_json(res)
                epics = self.fetch_jira_epics(parsed_data)
                json_res["channel_id"] = channel_id
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
        file_paths = glob(f"{os.getcwd()}/responses_v5/*.json")
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

def llm_res_to_csv(channel_id):
    desired_columns = ["channel_id","thread_ts","thread_data","merchant_id","errors","slack_url","order_id",
                       "session_id","llm_category","exact_error","thread_meta_data","llm_summary","epics",
                       "question","solution","rca_steps","questions_to_be_asked_for_rca"]
    dfs = []
    output_csv_path = f"{os.getcwd()}/data/{channel_id}.csv"
    out_dir = os.path.dirname(output_csv_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    file_paths = glob(f"{os.getcwd()}/responses_v5/{channel_id}/*.json")
    for idx,path in tqdm(enumerate(file_paths),total=len(file_paths)):
        with open(path,"r") as fp:
            slack_data = [json.load(fp)]
            df = pd.DataFrame(slack_data)
            df = df.reindex(columns=desired_columns)
            dfs.append(df)
    # Concatenate all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    # Save the combined DataFrame to a CSV file
    combined_df.to_csv(output_csv_path, index=False)
    print(f"Done creating csv for {channel_id}")

def main():
    parser = argparse.ArgumentParser()
    num_workers = mp.cpu_count()*2

    # Add arguments
    parser.add_argument("--env-path", help="ENV file path", required=True)
    parser.add_argument("--jira-epic", help="JIRA Epic Id", default=None)
    parser.add_argument("--jira-domain", help="JIRA domain", default=None)
    parser.add_argument("--slack-domain", help="slack domain", default=None)
    args = parser.parse_args()
    env_file_path = args.env_path
    load_dotenv(env_file_path,override=True)

    channel_ids = ast.literal_eval(os.getenv("SLACK_CHANNEL_ID"))

    if not args.jira_epic:
        slack = SlackScraper(args.slack_domain)
        print("Fetching slack thread ids ...")
        for channel in channel_ids:
            slack_data_dir = f"{os.getcwd()}/docs_v5/{channel}"
            json_dir = f"{os.getcwd()}/responses_v5/{channel}"
            for dir in [slack_data_dir,json_dir]:
                create_dir_if_missing(dir)
            thread_ts = slack.fetch_slack_thread_ids(channel,[])
            print(f"Done fetching slack thread ids for channel : {channel}")
            print(f"num of threads :: {len(thread_ts)}")
            with mp.Pool(num_workers) as pool:
                results = list(tqdm(
                    pool.imap(slack.get_model_results, thread_ts),
                    total=len(thread_ts),
                    desc='Fetching Model Responses'))
            print("Done writing files")
            llm_res_to_csv(channel)
            ## Merge Jira data with slack data
            # slack.merge_slack_jira_data()
    else:
        jira = JiraScraper(args.jira_domain)
        jira.fetch(args.jira_epic)


if __name__ == "__main__":
    main()