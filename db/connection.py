import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

# Global database connection
db_client = None
database = None

async def init_db():
    """Initialize MongoDB connection"""
    global db_client, database
    
    try:
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("DATABASE_NAME", "travel_planner")
        
        db_client = MongoClient(mongo_url)
        # Test connection
        db_client.admin.command('ping')
        
        database = db_client[db_name]
        logger.info(f"Connected to MongoDB database: {db_name}")
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

def get_db():
    """Return dummy db for testing or actual db if set."""
    if os.getenv("ENV") == "test":
        class DummyInsertResult:
            @property
            def inserted_id(self):
                return "dummy_id"

        class DummyCursor:
            def sort(self, *args, **kwargs):
                return self

            def limit(self, *args, **kwargs):
                return self

            async def to_list(self, length):
                return []

        class DummyCollection:
            def find_one(self, *args, **kwargs):
                return None

            def find(self, *args, **kwargs):
                return DummyCursor()

            def insert_one(self, *args, **kwargs):
                return DummyInsertResult()

            def update_one(self, *args, **kwargs):
                return None

            def delete_one(self, *args, **kwargs):
                class DummyDeleteResult:
                    deleted_count = 1
                return DummyDeleteResult()

            def count_documents(self, *args, **kwargs):
                return 0

            def aggregate(self, *args, **kwargs):
                return []

            def create_index(self, *args, **kwargs):
                return None

        class DummyDB:
            def __getitem__(self, name):
                return DummyCollection()

            def __getattr__(self, name):
                return DummyCollection()

            
        return DummyDB()

    # fallback to real database
    if database is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return database

def close_db():
    """Close database connection"""
    global db_client
    if db_client:
        db_client.close()
        logger.info("Database connection closed")