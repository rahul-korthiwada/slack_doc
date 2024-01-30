import requests
import json
import os

def post_request_to_chat_gpt(parsedData):
    api_key = os.getenv("OPEN_API_KEY")
    api_endpoint = 'https://api.openai.com/v1/chat/completions'
    model_name = 'gpt-4-1106-preview'


    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-4-1106-preview',
        'messages': [
            {'role': 'user', 'content': json.dumps(parsedData)},
            {'role': 'user', 'content': '''Can you provide a detailed summary for the above slack conversation. Pick the context from the appropriate messages and share summary in the following format:
                                            1. Summary of the problem being discussed on the thread
                                            2. What caused the issue/problem?
                                            3. Who got affected and what was the impact?
                                            4. Actual session information where the problem happened?
                                            5. What were the all the checks discussed(or suggested) on the thread to understand the problem better and root cause the issue?
                                            6. What are the final action steps taken to resolve the issue?
                                            7. What are the steps taken to resolve this issue with specific info on each step.
                                            8. What are the steps taken for better visibility and debugging.'''},
            # {'role':'user','content':'Hello'}
        ],
    }
    print("request_sent")
    print(json.dumps(data))
    response = requests.post(api_endpoint, headers=headers, json=data)
    print(response.json())
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