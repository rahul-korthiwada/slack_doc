
from slack import scrape_data_from_slack
from openai import post_request_to_chat_gpt

channel_id = "C023M6R5U1W"
ts = 1701337122.088149

parsed_data = scrape_data_from_slack(channel_id,ts)
api_response = post_request_to_chat_gpt(parsed_data)
if api_response is not None:
    with open("./docs/" + channel_id + "_" + str(ts) + ".txt", "w") as f:
        f.write(api_response) 