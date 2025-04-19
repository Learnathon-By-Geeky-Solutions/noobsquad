# core/email.py
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")

async def send_email(to: str, subject: str, body: str):
    configuration = Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY
    api_client = ApiClient(configuration)
    email_api = TransactionalEmailsApi(api_client)
    
    email = SendSmtpEmail(
        to=[{"email": to}],
        sender={"email": EMAIL_FROM, "name": "U-Connect"},
        subject=subject,
        text_content=body
    )
    
    try:
        response = email_api.send_transac_email(email)
        return response
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {str(e)}")
        raise RuntimeError(f"Failed to send email: {str(e)}")