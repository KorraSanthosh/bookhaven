import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load connection string from .env file
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "bookhaven")

if not MONGODB_URL:
    raise RuntimeError("MONGODB_URL not found in environment variables. Please check your .env file.")

# Motor client initialization
client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

async def get_db():
    """
    FastAPI dependency that returns the MongoDB database instance.
    Motor is naturally async and connection pooling is handled by the client.
    """
    return db

# Helper for migrations or direct collections
def get_collection(name: str):
    return db[name]
