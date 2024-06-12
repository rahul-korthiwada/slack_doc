import requests
import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv("../.env",override=True)

class LLM:
    def __init__(self) -> None:
        self.deployment_name = os.getenv("AZURE_GPT_DEPLOYMENT_NAME")
        self.openai_api_base = os.getenv("AZURE_OAI_BASE_URL")
        self.openai_api_key = os.getenv('AZURE_OAI_API_KEY')
        self.openai_api_version = os.getenv('AZURE_OAI_API_VERSION')

        self.client = AzureOpenAI(
            azure_endpoint= self.openai_api_base,
            azure_deployment= self.deployment_name,
            api_version= self.openai_api_version,
            api_key= self.openai_api_key
        )

    def post_request_to_model(self,data):
        messages = [
            {'role': 'user', 'content': json.dumps(data)},
            {'role': 'user', "content":
                '''
                    Answer the following questions for the above slack conversation.Pick the context from the appropriate messages and answer the following questions. Provide answer in valid json format. supress rows which are not valid json
                    
                    Merchant id: What is the merchant id being discussed ? use merchant_id as key
                    Main Errors: List all reported issues verbatim. use errors as key
                    Category: give a category to the issue discussed based on single main context. use llm_category as key
                    Exact Error: What are the exact error messages discussed in the conversation ? Answer in few words. Use exact_error as key
                    Thread Meta Data: What are the formatted keywords or sentences. Exclude links, mentions, slack users and channels. use thread_meta_data as key
                    Order id: Extract order id from the conversation. use order_id as key
                    Session id: Extract session id from the conversation. use session_id as key
                    User's Question: Rephrase the main issue as a question from the user's perspective. use question as key
                    Solution: Summarize the final resolution in a concise paragraph. use solution as key
                    RCA Steps: List all troubleshooting steps taken, in chronological order, using technical terms. use rca_steps as key
                    Questions To Be Asked: Generate at least 5 questions that an engineer would ask to debug this issue, focusing on: use questions_to_be_asked_for_rca as key
                        a. frame question such a way that rca steps would answer the question
                        b. Request validation
                        c. issue troubleshooting
                        d. Live environment testing
                        e. Attend to even minute details of troubleshooting.

                    Ensure each RCA question:

                    Is directly related to a step in the RCA process
                    Can be answered with yes/no or specific data
                    Uses technical terms from the payment industry
                    Guides towards the root cause incrementally
                    Does NOT involve post-implementation status

                    Can you provide a detailed summary for the above slack conversation. use llm_summary as key. Pick the context from the appropriate messages and share summary in the following format:
                        Summary of the problem being discussed on the thread
                        What caused the issue/problem?
                        Who got affected and what was the impact?
                        Actual session information where the problem happened?
                        What were the all the checks discussed(or suggested) on the thread to understand the problem better and root cause the issue?
                        What are the final action steps taken to resolve the issue?
                        What are the steps taken to resolve this issue with specific info on each step.
                        What are the steps taken for better visibility and debugging
                '''
                }
            ]
        response = self.client.chat.completions.create(
            model = self.deployment_name,
            messages = messages,
        )
        return (response.model_dump()["choices"][0]["message"]["content"])

    def to_json(self,response):
        start_index = response.find('```json') + len('```json')
        end_index = response.find('```', start_index)
        json_string = response[start_index:end_index].strip()
        try:
            json_data = json.loads(json_string)
            return json_data
        except Exception as ex:
            return {}

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
            ],
        }

        title_response = requests.post(api_endpoint, headers=headers, json=title_data)
        if title_response.status_code == 200:
            title_result = title_response.json()
            return (result['choices'][0]['message']['content'] , title_result['choices'][0]['message']['content'])
    else:
        print(f"Error: {response.status_code}, {response.text}")