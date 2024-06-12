import os
import sys
# sys.path.append(os.getcwd())
from slack_sdk import WebClient
from validation import mask_data
from utils import extract_slack_urls, extract_slack_details
from dotenv import load_dotenv
import time
from slack_sdk.errors import SlackApiError
import itertools

load_dotenv("../.env",override=True)

def scrape_child_data_from_slack(slack_url):
    max_retries = 5
    client = WebClient(token=os.getenv("SLACK_API_TOKEN"))
    slack_details = extract_slack_details(slack_url)
    if(len(slack_details) <= 0):
        return []
    channel = slack_details[0]['cid']
    # print("child channel :: ", channel)
    ts = slack_details[0]['ts']
    while max_retries >= 0:
        try:
            response = client.conversations_replies(channel=channel, ts=ts)
            break
        except SlackApiError as exception:
            # print("child max retries :: ",max_retries)
            time.sleep(2)
            max_retries -= 1
            if max_retries == 1:
                return []
            continue
    messages = [msg for msg in response['messages'] if 'subtype' not in msg]

    parsedData = []
    for message in messages:
        result, masked_text = mask_data(message['text'],"mask")
        user = ""
        if message.get('user') is not None:
            user = message['user'],
        else:
            print(message)
        messageInfo = {
            "message" : masked_text,
            "user" : user,
            "reactions" : message.get('reactions')
        }
    parsedData.append(messageInfo)
    return parsedData

def scrape_data_from_slack(channel,ts):
    max_retries = 5
    client = WebClient(token=os.getenv("SLACK_API_TOKEN"))
    while max_retries >= 0:
        try:
            response = client.conversations_replies(channel=channel, ts=ts)
            break
        except SlackApiError as exception:
            time.sleep(2)
            max_retries -= 1
            if max_retries ==1:
                return {"data":[],"additional_data":[]}
            continue

    messages = [msg for msg in response['messages'] if response["ok"] and "subtype" not in msg]

    childSlackUrls = set()
    parsedData = []
    for message in messages:
        result, masked_text = mask_data(message['text'],"mask")
        childSlackUrls = childSlackUrls.union(set(extract_slack_urls(message['text'])))
        user = ""
        if message.get('user') is not None:
            user = message['user'],
        else:
            print(message)
        messageInfo = {
            "message" : masked_text,
            "user" : user,
            "reactions" : message.get('reactions')
        }
        parsedData.append(messageInfo)

    additionalData = []
    for slackUrl in  childSlackUrls:
        additionalData.append(scrape_child_data_from_slack(slackUrl))

    return {
        'data' : parsedData,
        'additional_data' : list(itertools.chain.from_iterable(additionalData))
    }


def push_file(channel,ts,message,file_content, slack_thread_id):
    client = WebClient(token=os.getenv("SLACK_API_TOKEN"))
    try:
        response = client.files_upload_v2(
            channels="C06BS7J3X6Y",
            # thread_ts=ts,
            content=file_content.getvalue(),
            filename='summary.txt',
            initial_comment=message + "-- Slack Thread Id :- " + str(slack_thread_id)
        )
        print("File uploaded successfully")
    except Exception as e:
        print(f"Failed to upload file. Error: {e.response}")


