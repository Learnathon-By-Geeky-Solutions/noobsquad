from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class OTPVerificationRequest(BaseModel):
    email: str
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str