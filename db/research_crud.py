import logging
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from pymongo.errors import PyMongoError
from db.connection import get_db

logger = logging.getLogger(__name__)

async def save_research(research_data: Dict[str, Any]) -> str:
    """Save destination research to MongoDB"""
    try:
        db = get_db()
        collection = db.research
        
        research_data["created_timestamp"] = datetime.now(UTC).isoformat()
        
        result = collection.insert_one(research_data)
        logger.info(f"Research saved with ID: {result.inserted_id}")
        return str(result.inserted_id)
        
    except PyMongoError as e:
        logger.error(f"Database error saving research: {e}")
        raise
    except Exception as e:
        logger.error(f"Error saving research: {e}")
        raise

async def get_research_by_destination(destination: str, theme: str, num_days: int) -> Optional[Dict[str, Any]]:
    """Get cached research for a specific destination, theme, and num_days (used for caching)"""
    try:
        db = get_db()
        collection = db.research
        
        query = {
            "destination": destination.title(),
            "theme": theme,
            "num_days": num_days
        }
        
        result = collection.find_one(query, sort=[("created_timestamp", -1)])
        
        if result:
            result['_id'] = str(result['_id'])
            return result
            
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving research by destination: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving research by destination: {e}")
        return None

async def get_research_history_by_destination(destination: str, userid: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get research history for a specific destination and user"""
    try:
        db = get_db()
        collection = db.research
        
        query = {
            "destination": destination.title(),
            "userid": str(userid)
        }
        
        cursor = collection.find(
            query,
            {
                "destination": 1,
                "theme": 1,
                "num_days": 1,
                "budget": 1,
                "activities": 1,
                "created_timestamp": 1,
                "research_summary": 1,
                "attractions": 1,
                "cultural_info": 1
            }
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving research history: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving research history: {e}")
        return []

async def save_research_result(research_data: Dict[str, Any]) -> str:
    """Save research result to MongoDB (alias for save_research)"""
    return await save_research(research_data)