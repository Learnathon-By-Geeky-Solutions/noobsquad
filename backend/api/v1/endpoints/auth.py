from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.session import SessionLocal
import models.user as models
from schemas.auth import Token
from schemas.user import UserCreate, ProfileCompletionRequest
from core.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
import os
from dotenv import load_dotenv
from core.dependencies import get_db
import re

load_dotenv()

# Load secret key and algorithm from .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# OAuth2PasswordBearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Router
router = APIRouter()

allowed_keywords = ["stud", "edu", "university", "college", "ac", "edu", "institution"]
# ✅ Signup Route
@router.post("/signup/")
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the email domain contains any of the educational keywords
    if not any(keyword in user.email.lower() for keyword in allowed_keywords):
        raise HTTPException(status_code=400, detail="This is not an educational email address.")
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = hash_password(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        profile_completed=False  # ✅ Profile completion starts separately
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully. Please log in."}

# ✅ Login Route
@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ✅ Get Current User (Check Profile Status)
@router.get("/users/me/")
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Decode the token and log the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        

        username: str = payload.get("sub")
        
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError as e:
        print(f"JWT error: {str(e)}")  # Log the specific error for further insight
        raise HTTPException(status_code=401, detail="Invalid token")



