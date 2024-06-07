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