from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.session import SessionLocal
import models.user as models
from schemas.auth import Token
from schemas.user import UserCreate
from core.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
import os
from dotenv import load_dotenv


load_dotenv()  # Load environment variables

# Load secret key and algorithm from .env file
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# OAuth2PasswordBearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Router
router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Signup Route
@router.post("/signup/")
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = hash_password(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

# Login Route
@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# Protected Route

@router.get("/users/me/")

async def get_current_user(token: str = Depends(oauth2_scheme)):

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username = payload.get("sub")

        return {"username": username}

    except jwt.ExpiredSignatureError:

        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.PyJWTError:

        raise HTTPException(status_code=401, detail="Invalid token")
