import os
from slack_sdk import WebClient
import json
from validation import mask_data


def scrape_data_from_slack(channel,ts):
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    response = client.conversations_replies(channel=channel, ts=ts)
    messages = response["messages"]
    

    parsedData = []
    for message in messages:
        result, masked_text = mask_data(message['text'],"mask")
        messageInfo = {
            "message" : masked_text,
            "user" : message['user'],
            "reactions" : message.get('reactions')
        }
        parsedData.append(messageInfo)

    print(json.dumps(parsedData))
    return parsedData


