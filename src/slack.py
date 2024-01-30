import os
from slack_sdk import WebClient
from validation import mask_data
from utils import extract_slack_urls, extract_slack_details

def scrape_child_data_from_slack(slack_url):
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    slack_details = extract_slack_details(slack_url)
    if(len(slack_details) <= 0):
        return []
    channel = slack_details[0]['cid']
    ts = slack_details[0]['ts']
    print(ts)
    print(channel)
    try:
        response = client.conversations_replies(channel=channel, ts=ts)
    except Exception as e:
        print(f"Failed to get child thread info. Error: {e.response}")
        return []
    messages = response["messages"]
    print(messages)
    
    parsedData = []
    for message in messages:
        result, masked_text = mask_data(message['text'],"mask")
        messageInfo = {
            "message" : masked_text,
            "user" : message['user'],
            "reactions" : message.get('reactions')
        }
    parsedData.append(messageInfo)
    return parsedData
    
def scrape_data_from_slack(channel,ts):
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    response = client.conversations_replies(channel=channel, ts=ts)
    messages = response["messages"]
    
    childSlackUrls = set()
    parsedData = []
    for message in messages:
        result, masked_text = mask_data(message['text'],"mask")
        childSlackUrls = childSlackUrls.union(set(extract_slack_urls(message['text'])))
        messageInfo = {
            "message" : masked_text,
            "user" : message['user'],
            "reactions" : message.get('reactions')
        }
        parsedData.append(messageInfo)
    print(childSlackUrls)
    additionalData = []
    for slackUrl in  childSlackUrls:
        additionalData.append(scrape_child_data_from_slack(slackUrl))
    # print(json.dumps(parsedData))
    return {
        'data' : parsedData,
        'additional_data' : additionalData
    }
    

def push_file(channel,ts,message,file_content, slack_thread_id):
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
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


