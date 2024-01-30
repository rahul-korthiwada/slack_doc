import json
import base64
from urllib.parse import unquote
import urllib
from main import summarize
from utils import extract_slack_details

def lambda_handler(event, context):
    print(json.dumps(event))
    parsed_url = unquote(base64.b64decode(event['body']))
    print(parsed_url)
    channel_id, ts, slack_thread_id = extractDetailsFromSlackUrl(parsed_url)
    print(channel_id)
    print(ts)
    print(slack_thread_id)
    if(channel_id is None):
        return {
            'statusCode' : 400
        }
    summarize(channel_id,ts,slack_thread_id)
    return {
        'statusCode': 200
    }

def extractDetailsFromSlackUrl(parsed_url):
    try:
        channel_id = parsed_url.split("cid=")[1].split("&api_app_id")[0]
        channel_id = channel_id.strip(">")
        ts = parsed_url.split("?thread_ts=")[1].split("cid")[0]
        ts = ts.strip("amp;")
        ts = ts.strip("&")
        slack_thread_id = parsed_url.split("&text=")[1].split("?thread_ts=")[0] + "?thread_ts=" + str(ts) + "&cid=" + str(channel_id)
        return (channel_id, ts, slack_thread_id)
    except Exception as e:
        print("Thread ts is not present as parameter")
    try:
        slack_details = extract_slack_details(parsed_url)
        if(len(slack_details) <= 0):
            return None,None,None
        channel_id = slack_details[0]['cid']
        ts = slack_details[0]['ts']
        slack_thread_id = parsed_url.split("&text=")[1].split("&api_app_id=")[0]
        return (channel_id, ts, slack_thread_id)
    except Exception as e:
        print("Base Format also didn't match")
    
    return None,None,None
