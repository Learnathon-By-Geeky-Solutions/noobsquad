from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request
from sqlalchemy.orm import Session
from core.dependencies import get_db
from models.user import User
from services.AuthHandler import AuthHandler
from core.security import create_access_token
import os

router = APIRouter()

config_data = {
    "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
    "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
    "SECRET_KEY": os.getenv("SECRET_KEY", "secret"),
}
config = Config(environ=config_data)
oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=config_data["GOOGLE_CLIENT_ID"],
    client_secret=config_data["GOOGLE_CLIENT_SECRET"],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

@router.get("/login")
async def google_login(request: Request):
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    print("Google token response:", token)
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="No userinfo in Google response")    # Find or create user
    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        from core.security import hash_password
        # Generate a strong random password for Google OAuth users
        # They won't use this password since they'll always login via Google
        import secrets
        random_password = secrets.token_urlsafe(16)
        hashed_password = hash_password(random_password)
        
        # Create username from email and make it unique with a random suffix
        base_username = user_info["email"].split("@")[0]
        username = f"{base_username}{secrets.token_hex(3)}"
        
        user = User(
            username=username,
            email=user_info["email"],
            hashed_password=hashed_password,
            is_verified=True,
            profile_completed=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)# Generate JWT token
    access_token = create_access_token({"sub": user.username})
    # Redirect to frontend with token as query param
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(f"{frontend_url}/login?token={access_token}")