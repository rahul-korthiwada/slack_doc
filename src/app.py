import streamlit as st
from dotenv import load_dotenv
import os
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core import Settings, VectorStoreIndex, StorageContext, SimpleDirectoryReader
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv('../.env',override=True)

gpt_deployment_name = os.getenv("AZURE_GPT_DEPLOYMENT_NAME")
openai_api_base = os.getenv("AZURE_OAI_BASE_URL")
openai_api_key = os.getenv('AZURE_OAI_API_KEY')
openai_api_version = os.getenv('AZURE_OAI_API_VERSION')
embed_deployment_name = os.getenv("AZURE_EMB_DEPLOYMENT_NAME")

Settings.llm = AzureOpenAI(
    model="gpt-4",
    deployment_name=gpt_deployment_name,
    api_key=openai_api_key,
    azure_endpoint=openai_api_base,
    api_version=openai_api_version,
)
Settings.embed_model = AzureOpenAIEmbedding(
    model="text-embedding-ada-002",
    deployment_name=embed_deployment_name,
    api_key=openai_api_key,
    azure_endpoint=openai_api_base,
    api_version=openai_api_version,
)

# initialize client, setting path to save data
db = chromadb.PersistentClient(path="./chroma_db")

# create collection
chroma_collection = db.get_or_create_collection("dre_helper")

# assign chroma as the vector_store to the context
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# create your index
index = VectorStoreIndex.from_vector_store(
    vector_store, storage_context=storage_context
)

chat_engine_2 = index.as_chat_engine(
    context_prompt=(
        "You are a chatbot, able to have normal interactions, as well as "
        " provide the cause of issues based on the given context."
        "Here are the relevant documents for the context:\n"
        "{context_str}"
        "\nInstruction: Use the previous chat history, or the context above, to interact and help the user."
        "\nDo not mention ids from the conversations"
    ),
    chat_mode="condense_plus_context", streaming=True,
    similarity_top_k=5
)
# response_stream = chat_engine_2.stream_chat("why am i facing internal server error for orders")
# response_stream.print_response_stream()

# # create a query engine and query
# query_engine = index.as_query_engine()

st.title("Debug Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask Anything"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = chat_engine_2.stream_chat(prompt)
    with st.chat_message("assistant"):
        st.write_stream(response.response_gen)
    st.session_state.messages.append({"role": "assistant", "content": response})
