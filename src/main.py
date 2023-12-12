
from slack import scrape_data_from_slack
from chatai import post_request_to_chat_gpt
import json

channel_id = "C023M6R5U1W"
ts = 1701337122.088149

parsed_data = scrape_data_from_slack(channel_id,ts)
api_response = post_request_to_chat_gpt(parsed_data)
print(api_response)
# if api_response is not None:
#     [content, title] = api_response 
#     with open("./" + title + ".txt/" + channel_id + "_" + str(ts) + ".txt", "w") as f:
#         f.write(content) 