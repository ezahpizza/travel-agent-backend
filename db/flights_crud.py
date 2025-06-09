import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
from pymongo.errors import PyMongoError

from db.connection import get_db

logger = logging.getLogger(__name__)

async def save_flight_search(search_data: Dict[str, Any]) -> str:
    """Save flight search results to MongoDB"""
    try:
        db = get_db()
        collection = db.flights
        
        result = collection.insert_one(search_data)
        logger.info(f"Flight search saved with ID: {result.inserted_id}")
        return str(result.inserted_id)
        
    except PyMongoError as e:
        logger.error(f"Database error saving flight search: {e}")
        raise
    except Exception as e:
        logger.error(f"Error saving flight search: {e}")
        raise

async def get_flight_search_by_params(source: str, destination: str, departure_date, return_date, 
                                    hours_threshold: int = 2) -> Optional[Dict[str, Any]]:
    """Get cached flight search results if recent enough"""
    try:
        db = get_db()
        collection = db.flights
        
        # Check for recent searches (within threshold hours)
        threshold_time = datetime.now(UTC) - timedelta(hours=hours_threshold)
        
        query = {
            "source": source.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date.isoformat(),
            "return_date": return_date.isoformat(),
            "search_timestamp": {"$gte": threshold_time.isoformat()}
        }
        
        result = collection.find_one(query, sort=[("search_timestamp", -1)])
        
        if result:
            result['_id'] = str(result['_id'])
            logger.info(f"Found cached flight search for {source}-{destination}")
            return result
            
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving flight search: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving flight search: {e}")
        return None

async def get_recent_flight_searches(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent flight searches for history"""
    try:
        db = get_db()
        collection = db.flights
        
        cursor = collection.find(
            {},
            {
                "source": 1,
                "destination": 1,
                "departure_date": 1,
                "return_date": 1,
                "search_timestamp": 1,
                "metadata.processed_count": 1
            }
        ).sort("search_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving flight history: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving flight history: {e}")
        return []

async def delete_old_flight_searches(days_old: int = 30) -> int:
    """Delete flight searches older than specified days"""
    try:
        db = get_db()
        collection = db.flights
        
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)
        
        result = collection.delete_many({
            "search_timestamp": {"$lt": cutoff_date.isoformat()}
        })
        
        logger.info(f"Deleted {result.deleted_count} old flight searches")
        return result.deleted_count
        
    except PyMongoError as e:
        logger.error(f"Database error deleting old searches: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error deleting old searches: {e}")
        return 0