from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load the .env file for local development
load_dotenv()

# Check the environment (local or CI/CD)
environment = os.getenv("ENV", "local")

# Determine the DATABASE_URL based on the environment
if environment == "ci":
    # For CI/CD, the DATABASE_URL can be set in GitHub Secrets or environment variables
    DATABASE_URL = os.getenv("CI_DATABASE_URL", "postgresql://sonar:sonar@localhost:5432/sonar")
else:
    # For local development, fallback to the DATABASE_URL in the .env file
    DATABASE_URL = os.getenv("DATABASE_URL")

# Setup SQLAlchemy engine with the appropriate DATABASE_URL
engine = create_engine(DATABASE_URL)

# Create sessionmaker for database interaction
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare a base class for model creation
Base = declarative_base()
