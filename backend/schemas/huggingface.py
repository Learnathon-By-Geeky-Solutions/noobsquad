from pydantic import BaseModel

class PromptRequest(BaseModel):
    input: str

class PromptResponse(BaseModel):
    response: str

class BotResponse(BaseModel):
    response: str  # ✅ Only serializable fields