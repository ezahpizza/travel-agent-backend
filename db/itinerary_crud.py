import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
from pymongo.errors import PyMongoError
from bson import ObjectId
from bson.errors import InvalidId

from db.connection import get_db
from utils.serialization_utils import serialize_for_mongo, log_exception

logger = logging.getLogger(__name__)

async def save_itinerary(itinerary_data: Dict[str, Any]) -> str:
    """Save generated itinerary to MongoDB"""
    try:
        db = get_db()
        collection = db.itineraries

        itinerary_data["created_timestamp"] = datetime.now(UTC).isoformat()
        itinerary_data["userid"] = str(itinerary_data.get("userid", ""))
        mongo_data = serialize_for_mongo(itinerary_data)
        result = collection.insert_one(mongo_data)
        logger.info(f"Itinerary saved with ID: {result.inserted_id}")
        return str(result.inserted_id)
    except PyMongoError as e:
        log_exception(logger, "Database error saving itinerary", e)
        raise
    except Exception as e:
        log_exception(logger, "Error saving itinerary", e)
        raise

async def get_itineraries_by_params(destination: str, theme: str, num_days: int,
                                  userid: str, hours_threshold: int = 24) -> Optional[Dict[str, Any]]:
    """Get cached itinerary if recent enough"""
    try:
        db = get_db()
        collection = db.itineraries
        # Input validation and sanitization
        if not isinstance(destination, str) or not isinstance(theme, str):
            logger.error("Invalid input types for destination or theme")
            return None
        threshold_time = datetime.now(UTC) - timedelta(hours=hours_threshold)
        query = {
            "destination": destination.title(),
            "theme": theme,
            "num_days": num_days,
            "created_timestamp": {"$gte": threshold_time.isoformat()},
            "userid": str(userid)
        }
        result = collection.find_one(query, sort=[("created_timestamp", -1)])
        if result:
            result['_id'] = str(result['_id'])
            logger.info(f"Found cached itinerary for {destination}")
            return result
        return None
    except PyMongoError as e:
        logger.error(f"Database error retrieving cached itinerary: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving cached itinerary: {e}")
        return None

async def get_recent_itineraries_by_user(userid: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent itineraries for a specific user"""
    try:
        db = get_db()
        collection = db.itineraries
        
        cursor = collection.find(
            {"userid": str(userid)},
            {"created_timestamp": 1}
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving user itineraries: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving user itineraries: {e}")
        return []

async def get_itinerary_by_id(itinerary_id: str, userid: str) -> Optional[Dict[str, Any]]:
    """Get a specific itinerary by ID and user ID"""
    try:
        db = get_db()
        collection = db.itineraries
        
        # Convert string ID to ObjectId for MongoDB query
        try:
            object_id = ObjectId(itinerary_id)
        except InvalidId:
            logger.error(f"Invalid itinerary ID format: {itinerary_id}")
            return None
            
        result = collection.find_one({
            "_id": object_id,
            "userid": str(userid)
        })
        
        if result:
            result['_id'] = str(result['_id'])
            logger.info(f"Found itinerary {itinerary_id} for user {userid}")
            return result
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving itinerary {itinerary_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving itinerary {itinerary_id}: {e}")
        return None
    
async def delete_itinerary(itinerary_id: str, userid: str) -> bool:
    """Delete an itinerary"""
    try:
        db = get_db()
        collection = db.itineraries
        
        # Convert string ID to ObjectId
        try:
            object_id = ObjectId(itinerary_id)
        except InvalidId:
            logger.error(f"Invalid itinerary ID format: {itinerary_id}")
            return False
        
        result = collection.delete_one({
            "_id": object_id,
            "userid": str(userid)
        })
        
        if result.deleted_count > 0:
            logger.info(f"Itinerary deleted: {itinerary_id}")
            return True
        else:
            logger.warning(f"No itinerary found to delete: {itinerary_id}")
            return False
            
    except PyMongoError as e:
        logger.error(f"Database error deleting itinerary: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting itinerary: {e}")
        return False

async def delete_old_itineraries(days_old: int = 90) -> int:
    """Delete itineraries older than specified days"""
    try:
        db = get_db()
        collection = db.itineraries
        
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)
        
        result = collection.delete_many({
            "created_timestamp": {"$lt": cutoff_date.isoformat()}
        })
        
        logger.info(f"Deleted {result.deleted_count} old itineraries")
        return result.deleted_count
        
    except PyMongoError as e:
        logger.error(f"Database error deleting old itineraries: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error deleting old itineraries: {e}")
        return 0

async def get_itinerary_stats() -> Dict[str, Any]:
    """Get statistics about itineraries"""
    try:
        db = get_db()
        collection = db.itineraries
        
        total_itineraries = collection.count_documents({})
        
        # Popular destinations
        popular_destinations = list(collection.aggregate([
            {"$group": {"_id": "$destination", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]))
        
        # Popular themes
        popular_themes = list(collection.aggregate([
            {"$group": {"_id": "$theme", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]))
        
        # Average trip duration
        avg_duration = list(collection.aggregate([
            {"$group": {"_id": None, "avg_days": {"$avg": "$num_days"}}}
        ]))
        
        # Recent activity
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        recent_itineraries = collection.count_documents({
            "created_timestamp": {"$gte": seven_days_ago.isoformat()}
        })
        
        return {
            "total_itineraries": total_itineraries,
            "popular_destinations": [{"destination": item["_id"], "count": item["count"]} for item in popular_destinations],
            "popular_themes": [{"theme": item["_id"], "count": item["count"]} for item in popular_themes],
            "average_trip_duration": round(avg_duration[0]["avg_days"], 1) if avg_duration else 0,
            "recent_itineraries_7_days": recent_itineraries
        }
        
    except PyMongoError as e:
        logger.error(f"Database error getting itinerary stats: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error getting itinerary stats: {e}")
        return {}

# Ensure indexes for performance (run once at startup or in a setup script)
def ensure_indexes():
    db = get_db()
    collection = db.itineraries
    collection.create_index([("destination", 1), ("theme", 1), ("num_days", 1), ("created_timestamp", -1)])