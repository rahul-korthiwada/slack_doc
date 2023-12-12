from openai import OpenAI
import time
client = OpenAI()
# Add the file to the assistant
assistant = client.beta.assistants.create(
    instructions="You are a slack conversation analysis chatbot, The Json contains the slack thread summary of the conversation. Json Format :-  Array Of Messages, Each Message contains message, the user who posted it and the peoples reactions.",
    model="gpt-4-1106-preview",
    tools=[{"type": "retrieval"}]
)

def post_request_to_chat_gpt(file_name):

# Upload a file with an "assistants" purpose
    file1 = client.files.create(
        file=open("tmp.json", "rb"),
        purpose='assistants'
    )
    print(file1)

    thread = client.beta.threads.create(
        messages=[
            {
            "role": "user",
            "content": "Analytics Bot",
            "file_ids": [file1.id]
            }
        ]
    )

    create_run(thread,"Analyse the Slack Summary we have attatched as a file in this thread and Please provide the summary in the following format 1. Summary of the problem 2. Why it has happened 3. Different Kind Of Solutions 4. Actionables 5.Actual Session Information")
    create_run(thread,"Please provide the title for the above document in just one word")

    thread_messages = client.beta.threads.messages.list(thread.id)
    print(thread_messages.data)
    if(len(thread_messages.data) >= 2):
        content = thread_messages.data[1].content.text
        title = thread_messages.data[0].content.text
        return (content,title)

def create_run(thread,instruction):
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions = instruction
    )
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        print("Current Thread Status", run.status)
        if run.status == "completed":
            break
        time.sleep(1)



# import requests
# import json
# import os

# def post_request_to_chat_gpt(parsedData):
#     api_key = os.getenv("OPEN_API_KEY")
#     api_endpoint = 'https://api.openai.com/v1/chat/completions'
#     model_name = 'gpt-3.5-turbo'


#     headers = {
#         'Authorization': f'Bearer {api_key}',
#         'Content-Type': 'application/json'
#     }

#     data = {
#         'model': 'gpt-3.5-turbo',
#         'messages': [
#             {'role': 'user', 'content': json.dumps(parsedData)},
#             {'role': 'user', 'content': 'Can you provide a detailed information for the above Slack Conversation, Json Format :-  Array Of Messages, Each Message contains message, the user who posted it and the peoples reactions. Please provide the summary in the following format 1. Summary of the problem 2. Why it has happened 3. Different Kind Of Solutions 4. Actionables 5.Actual Session Information'},
#             # {'role':'user','content':'Hello'}
#         ],
#     }

#     response = requests.post(api_endpoint, headers=headers, json=data)

#     if response.status_code == 200:
#         result = response.json()
#         title_data = {
#             'model': 'gpt-3.5-turbo',
#             'messages': [
#                 {'role': 'user', 'content': 'Can you suggest a title for the above discussion'},
#                 # {'role':'user','content':'Hello'}
#             ],
#         }

#         title_response = requests.post(api_endpoint, headers=headers, json=title_data)
#         if title_response.status_code == 200:
#             title_result = title_response.json()
#             return (result['choices'][0]['message']['content'] , title_result['choices'][0]['message']['content'])
#     else:
#         print(f"Error: {response.status_code}, {response.text}")
    