import requests
import json
import os

def post_request_to_chat_gpt(parsedData):
    api_key = os.getenv("OPEN_API_KEY")
    api_endpoint = 'https://api.openai.com/v1/chat/completions'
    model_name = 'gpt-3.5-turbo'


    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {'role': 'user', 'content': json.dumps(parsedData)},
            {'role': 'user', 'content': 'Can you provide a detailed information for the above Slack Conversation, Json Format :-  Array Of Messages, Each Message contains message, the user who posted it and the peoples reactions. Please provide the summary in the following format 1. Summary of the problem 2. Why it has happened 3. Different Kind Of Solutions 4. Actionables 5.Actual Session Information'},
            # {'role':'user','content':'Hello'}
        ],
    }

    response = requests.post(api_endpoint, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        title_data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'user', 'content': 'Can you suggest a title for the above discussion'},
                # {'role':'user','content':'Hello'}
            ],
        }

        title_response = requests.post(api_endpoint, headers=headers, json=title_data)
        if title_response.status_code == 200:
            title_result = title_response.json()
            return (result['choices'][0]['message']['content'] , title_result['choices'][0]['message']['content'])
    else:
        print(f"Error: {response.status_code}, {response.text}")