# apiresponse.py
from fastapi import APIRouter, Query
from schemas.chatbot import QuestionInput
from langchain_community.tools import WikipediaQueryRun, ArxivQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain import hub
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools.retriever import create_retriever_tool
import os
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")

wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=250))
arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=200))

loader = PyPDFLoader("attention.pdf")
docs = loader.load()
chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)
db = FAISS.from_documents(chunks, OllamaEmbeddings())

retriever = db.as_retriever()
pdf_tool = create_retriever_tool(
    retriever=retriever,
    name="attention_paper_search",
    description="Searches the attention paper for relevant information."
)

tools=[pdf_tool,wiki,arxiv]

llm = Ollama(model="llama3.2")
prompt = hub.pull("hwchase17/openai-tools-agent")
agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

@router.post("/ask")
async def ask_question(query: QuestionInput):
    try:
        response = agent_executor.invoke({"input": query.question})
        return {"response": response["output"]}
    except Exception as e:
        return {"error": str(e)}


