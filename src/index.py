from dotenv import load_dotenv
import os

load_dotenv('../.env',override=True)

gpt_deployment_name = os.getenv("AZURE_GPT_DEPLOYMENT_NAME")
openai_api_base = os.getenv("AZURE_OAI_BASE_URL")
openai_api_key = os.getenv('AZURE_OAI_API_KEY')
openai_api_version = os.getenv('AZURE_OAI_API_VERSION')
embed_deployment_name = os.getenv("AZURE_EMB_DEPLOYMENT_NAME")

from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader

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

documents = SimpleDirectoryReader("./docs").load_data()
vector_index = VectorStoreIndex.from_documents(documents)
vector_index.storage_context.persist(persist_dir="./indexes/index_from_documents")
query_engine = vector_index.as_query_engine()

response = query_engine.query("can you suggest solutions for merchant account not found issue")
print(response)

import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext

# initialize client, setting path to save data
db = chromadb.PersistentClient(path="./chroma_db")

# create collection
chroma_collection = db.get_or_create_collection("slack_helper")

# assign chroma as the vector_store to the context
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

doc_index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context
)

v_index = VectorStoreIndex.from_vector_store(
    vector_store, storage_context=storage_context
)

# create a query engine
query_engine_2 = v_index.as_query_engine()
response = query_engine_2.query("can you suggest solutions for merchant account not found issue")
print(response)