import json
import base64
from urllib.parse import unquote
import urllib
from main import summarize

def lambda_handler(event, context):
    parsed_url = urllib.parse.urlparse(unquote(base64.b64decode(event['body'])))
    channel_id = urllib.parse.parse_qs(parsed_url.path)['cid'][0]
    ts = urllib.parse.parse_qs(parsed_url.path)['thread_ts'][0]
    summarize(channel_id,ts)
    return {
        'statusCode': 200
    }
