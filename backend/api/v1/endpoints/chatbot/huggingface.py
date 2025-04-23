import os
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

hf_key = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"]= hf_key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


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
import re

from langchain_ollama import OllamaEmbeddings
router = APIRouter()


gemini_model = genai.GenerativeModel("gemini-2.0-flash")


import fitz  # PyMuPDF

# Global store: user_id -> chat_session and retriever
user_sessions = {}

# -------------------- Helpers --------------------

def extract_text_from_pdf(file: UploadFile):
    doc = fitz.open(stream=file.file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def create_retriever(text: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.create_documents([text])

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en",
        model_kwargs={"device": "cpu"}
    )

    db = FAISS.from_documents(docs, embeddings)
    retriever = db.as_retriever()
    return retriever

def remove_duplicate_qa(text):
    # Keep only the last Helpful Answer
    answers = re.findall(r"Helpful Answer: (.*)\n?(?=(Follow Up Input:|$))", text, re.DOTALL)
    if answers:
        return answers[-1][0].strip()
    return text.strip()

# -------------------- Endpoints --------------------

@router.post("/upload_pdf/", response_model=BotResponse)
async def upload_pdf(file: UploadFile, current_user: User = Depends(get_current_user)):
    text = extract_text_from_pdf(file)
    retriever = create_retriever(text)

    # Start chat session for user
    chat = gemini_model.start_chat(history=[])
    user_sessions[current_user.id] = {
        "chat": chat,
        "retriever": retriever
    }

    return {"response": "PDF uploaded and AI expert is ready to help you."}


@router.post("/hugapi", response_model=PromptResponse)
def api_response(
    req: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    session = user_sessions.get(current_user.id)

    if session is None:
        # No uploaded PDF, so just ask Gemini directly
        response = gemini_model.generate_content(req)
        return {"response": response.text.strip()}

    # Retrieve related documents from FAISS
    retriever = session["retriever"]
    related_docs = retriever.get_relevant_documents(req)
    context = "\n\n".join([doc.page_content for doc in related_docs])

    # Append context to query
    full_prompt = f"""You are an assistant answering questions based on the following context:
---
{context}
---
Now answer this question: {req}"""

    # Use the existing chat session for context-aware responses
    chat = session["chat"]
    response = chat.send_message(full_prompt)
    return {"response": response.text.strip()}