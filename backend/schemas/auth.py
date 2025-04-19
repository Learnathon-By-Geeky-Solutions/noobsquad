from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class OTPVerificationRequest(BaseModel):
    email: str
    otp: str