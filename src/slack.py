import os
from slack_sdk import WebClient
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

    # print(json.dumps(parsedData))
    return parsedData

def push_file(channel,ts,message,file_path):
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    try:
        response = client.files_upload_v2(
            channels=channel,
            thread_ts=ts,
            file=file_path,
            initial_comment=message
        )
        print("File uploaded successfully")
    except Exception as e:
        print(f"Failed to upload file. Error: {e.response['error']}")


