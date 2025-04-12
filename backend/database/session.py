from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Check the environment (local or CI/CD)
environment = os.getenv("ENV", "local")

# Determine the DATABASE_URL based on the environment
if environment == "ci":
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    # Fallback to local DATABASE_URL if not in CI/CD environment
    DATABASE_URL = os.getenv("DATABASE_URL")

# Setup SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create sessionmaker for database interaction
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare a base class for model creation
Base = declarative_base()
