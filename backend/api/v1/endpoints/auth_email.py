import os
import json
import pickle
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest

# FastAPI instance
app = FastAPI()

# OAuth 2.0 configuration
CLIENT_SECRET_FILE = "credentials.json"  # Your credentials.json file
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Step 1: Redirect user to Google's OAuth 2.0 server
@app.get("/authorize")
async def authorize():
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = 'http://localhost:8000/callback'
    
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    
    return RedirectResponse(authorization_url)

# Step 2: Handle OAuth 2.0 callback
@app.get("/callback")
async def oauth_callback(request: Request):
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = 'http://localhost:8000/callback'
    
    # Get authorization code
    authorization_response = str(request.url)
    
    # Exchange authorization code for credentials
    flow.fetch_token(authorization_response=authorization_response)
    
    # Save the credentials in a pickle file for later use
    credentials = flow.credentials
    with open("token.pickle", "wb") as token:
        pickle.dump(credentials, token)
    
    return {"message": "Authentication successful. You can now send OTP emails."}

# Step 3: Send OTP Email
def send_otp_email(to_email, otp):
    # Load the credentials from the pickle file
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)
    
    if not credentials or credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleRequest())
    
    # Build the Gmail API service
    service = build('gmail', 'v1', credentials=credentials)
    
    # Create the email content
    message = MIMEText(f"Your OTP is: {otp}")
    message['to'] = to_email
    message['from'] = "your-email@gmail.com"
    message['subject'] = "Your OTP for Verification"
    
    # Send the email using Gmail API
    try:
        send_message = service.users().messages().send(userId="me", body={'raw': message.as_string()}).execute()
        print(f"Message sent successfully: {send_message['id']}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Main route for OTP email request (example)
@app.post("/send-otp/{email}")
async def send_otp(email: str):
    otp = str(random.randint(100000, 999999))
    send_otp_email(email, otp)
    return {"message": "OTP sent successfully."}
