from pydantic import BaseModel

# Define the input model for the API
class QuestionInput(BaseModel):
    question: str