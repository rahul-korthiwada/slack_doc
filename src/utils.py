import json
from urllib.parse import unquote_plus
from config import *
#from .validation import *
import re
import gzip
import os

#return true and keyword found else return false and "Manual intervention" 
def distance(keylist,line,position):
    # print(keylist)
    for item in keylist:
        #index = line.casefold().find(item)
        index = re.finditer(item,line.casefold())
        # print(item,index)
        
        for i in index:
            if position-i.span()[1] < spanning_distance and position-i.span()[1] >= 0:
                # print(item)
                # print("spanning_distance")
                # print(position-i.span()[1] < spanning_distance)
                # for checking if the spanning distance is less
                if not ((line.casefold()[i.span()[1]].isalnum()) or line.casefold()[i.span()[1]] == '_'):
                    # print(line.casefold()[i.span()[1]]) if the next character to keyword is some alphanum
                    if i.span()[0]>0:
                        if not (line.casefold()[i.span()[0]-1].isalnum() or line.casefold()[i.span()[0]-1] == '_'):
                            # print(line.casefold()[i.span()[0]-1]) if the previous character is some alphanum
                            # print(item)
                            return True, item
                    else:
                        return True, item
    return False, "Manual Intervention required"



def eliminate(line,list_substr):
    for substr in list_substr:
        line = line.replace(substr[0],substr[1])
    return line

def extract_slack_urls(text):
    # Regular expression pattern for Slack URLs
    # This pattern assumes URLs like 'https://<workspace>.slack.com/archives/<channel>/<messageID>'
    # Adjust the pattern if you have different URL structures
    pattern = r"https://[\w.-]+\.slack\.com/archives/[\w-]+/[\w-]+"
    
    # Find all matches in the text
    slack_urls = re.findall(pattern, text)
    
    return slack_urls

def extract_slack_details(text):
    # Regular expression pattern for Slack URLs with groups for channel ID and messageID
    # This pattern assumes URLs like 'https://<workspace>.slack.com/archives/<channel>/<messageID>'
    pattern = r"https://[\w.-]+\.slack\.com/archives/(?P<channel_id>[\w-]+)/(?P<message_id>[\w-]+)"
    
    # Find all matches in the text
    matches = re.finditer(pattern, text)
    
    # Extract channel IDs and message IDs
    details = [{'cid': match.group('channel_id'), 'ts': match.group('message_id')[1:-6] + "." + match.group('message_id')[-6:]} for match in matches]
    
    return details
    