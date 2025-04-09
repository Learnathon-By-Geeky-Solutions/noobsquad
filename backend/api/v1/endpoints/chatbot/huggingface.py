import os
from dotenv import load_dotenv
load_dotenv()

hf_key = os.getenv("HUGGINGFACE_API_KEY")
os.environ["HUGGINGFACE_API_KEY"]= hf_key
os.environ["LANGCHAIN_TRACING_V2"]="true"

from fastapi import APIRouter,UploadFile, File, Form, Depends, HTTPException
from schemas.huggingface import PromptRequest, PromptResponse, BotResponse
from core.dependencies import get_db
from api.v1.endpoints.auth import get_current_user  # Authentication dependency
from models.user import User  # ✅ Correct model import
from sqlalchemy.orm import Session
from langchain_huggingface import HuggingFaceEndpoint
from huggingface_hub import InferenceClient
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import HuggingFaceHub
from langchain.memory import ConversationBufferMemory
from langchain_ollama import OllamaEmbeddings
router = APIRouter()

client = InferenceClient(token=hf_key)

model = "deepseek-ai/DeepSeek-V3-0324"
llm = HuggingFaceEndpoint(
    model=model,
    task="text-generation",  # Explicitly specify the task"
    max_new_tokens=200,
    temperature=0.7,
    huggingfacehub_api_token=hf_key
)


import fitz  # PyMuPDF

# Step 1: Extract text from uploaded PDF
def extract_text_from_pdf(file: UploadFile):
    doc = fitz.open(stream=file.file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Step 2: Create a Conversational QA Chain
def create_qa_chain(text: str):
    # Text splitting
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.create_documents([text])

    # Embedding
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en",model_kwargs={"device": "cpu"})

    db = FAISS.from_documents(docs, embeddings)
    retriever = db.as_retriever()

    # Cloud-based LLM from Hugging Face Hub
    llm = HuggingFaceHub(
        repo_id="deepseek-ai/DeepSeek-V3-0324",
        model_kwargs={"temperature": 0.5, "max_new_tokens": 512},huggingfacehub_api_token=hf_key
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, k=5)

    # QA chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
    )
    return qa_chain

# Global variable to store the chain (in-memory, for demo)
qa_chain = None
user_chains = {}  # user_id -> qa_chain

import re

def remove_duplicate_qa(text):
    # Keep only the last Helpful Answer
    answers = re.findall(r"Helpful Answer: (.*?)\n?(?=(Follow Up Input:|$))", text, re.DOTALL)
    if answers:
        return answers[-1][0].strip()
    return text.strip()


@router.post("/upload_pdf/", response_model=BotResponse)
async def upload_pdf(file: UploadFile, current_user: User = Depends(get_current_user)):
    text = extract_text_from_pdf(file)
    qa_chain = create_qa_chain(text)
    user_chains[current_user.id] = qa_chain
    return {"response": "PDF uploaded and QA chain created successfully."}



@router.post("/hugapi", response_model=PromptResponse)
def api_response(
    req: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    qa_chain = user_chains.get(current_user.id)
    if qa_chain is None:
        response = client.text_generation(req, model="deepseek-ai/DeepSeek-V3-0324")
        clean_response = remove_duplicate_qa(response)
        return {"response": clean_response}

    response = qa_chain.run(req)
    clean_response = remove_duplicate_qa(response)
    return {"response": clean_response}