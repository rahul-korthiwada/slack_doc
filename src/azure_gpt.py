import requests
import json
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
from pathlib import Path
from slack import scrape_data_from_slack


load_dotenv("../.env",override=True)


def post_request_to_azure_gpt(parsedData):
    deployment_name = os.getenv("AZURE_GPT_DEPLOYMENT_NAME")
    openai_api_base = os.getenv("AZURE_OAI_BASE_URL")
    openai_api_key = os.getenv('AZURE_OAI_API_KEY')
    openai_api_version = os.getenv('AZURE_OAI_API_VERSION')

    client = AzureOpenAI(
        azure_endpoint= openai_api_base,
        azure_deployment= deployment_name,
        api_version= openai_api_version,
        api_key= openai_api_key
    )

    messages = [
            {'role': 'user', 'content': json.dumps(parsedData)},
            {'role': 'user', "content": '''Answer the following questions for the above slack conversation.
                Pick the context from the appropriate messages and answer the following questions. Provide answer in valid json format. supress rows which are not valid json
                What is the service/merchant id being discussed ? use service/merchant_id as key
                What are the errors encountered ? Use minimal words. use errors as key
                give a category to the issue discussed based on single main context. use category as key
                What are the exact error messages discussed in the conversation ? Answer in few words. Use exact_error as key
                What are the formatted keywords or sentences. Exclude links, mentions, slack users and channels. use thread_meta_data as key
                Extract order id from the conversation.
                Extract session id from the conversation.
                Can you provide a detailed summary for the above slack conversation. use summary as key. Pick the context from the appropriate messages and share summary in the following format:
                    Summary of the problem being discussed on the thread
                    What caused the issue/problem?
                    Who got affected and what was the impact?
                    Actual session information where the problem happened?
                    What were the all the checks discussed(or suggested) on the thread to understand the problem better and root cause the issue?
                    What are the final action steps taken to resolve the issue?
                    What are the steps taken to resolve this issue with specific info on each step.
                    What are the steps taken for better visibility and debugging
                '''}
        ]
    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
    )
    return (response.model_dump()["choices"][0]["message"]["content"])

def convert_response_to_json(res):
  start_index = res.find('```json') + len('```json')
  end_index = res.find('```', start_index)
  json_string = res[start_index:end_index].strip()
  try:
    json_data = json.loads(json_string)
    return json_data
  except Exception as ex:
    return {}

def create_directory_if_missing(file_path):
  dir = os.path.dirname(file_path)
  if not os.path.exists(dir):
    os.makedirs(dir)

def write_to_file(file_path,data):
  create_directory_if_missing(file_path)
  with open(file_path,"w") as fp:
    fp.write(data)


def fetch_gpt_response(ts):
  channel_id = "C0107NB549K"
  base_dir = os.getcwd()
  gpt_res_file_path,res_json_path = os.getcwd() + "/gpt_responses_new/" + ts + ".txt", os.getcwd() + "/response_json/" + ts + ".json"
  slack_data_path = base_dir + "/docs/" + ts + ".md"
  try:
    parsed_data = scrape_data_from_slack(channel_id,ts)
    if any(parsed_data.values()):
      print(f"writing slack data to {ts}.md")
      write_to_file(slack_data_path,json.dumps(parsed_data))
    res = post_request_to_azure_gpt(parsed_data)
    print(f"writing gpt file to {gpt_res_file_path}")
    write_to_file(gpt_res_file_path,res)
    res_json = convert_response_to_json(res)
    res_json["channel_id"] = channel_id
    res_json["thread_ts"] = ts
    res_json["data"] = parsed_data
    print(f"writing json file to {res_json_path}")
    write_to_file(res_json_path,json.dumps(res_json))
  except Exception as ex:
    print("Exception ", ex, " in ", ts)
  return None
