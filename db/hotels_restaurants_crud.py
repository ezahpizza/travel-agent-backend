import logging
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Any, Optional
from pymongo.errors import PyMongoError

from db.connection import get_db

logger = logging.getLogger(__name__)

async def save_hotels_restaurants_search(search_data: Dict[str, Any]) -> str:
    """Save hotels and restaurants search results to MongoDB"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        # Ensure all datetime fields are ISO strings
        search_data["search_timestamp"] = datetime.now(UTC).isoformat()
        
        result = collection.insert_one(search_data)
        logger.info(f"Hotels & restaurants search saved with ID: {result.inserted_id}")
        return str(result.inserted_id)
        
    except PyMongoError as e:
        logger.error(f"Database error saving hotels & restaurants search: {e}")
        raise
    except Exception as e:
        logger.error(f"Error saving hotels & restaurants search: {e}")
        raise

async def get_hotels_restaurants_by_params(destination: str, theme: str, hotel_rating: str, 
                                         hours_threshold: int = 6) -> Optional[Dict[str, Any]]:
    """Get cached hotels and restaurants search results if recent enough"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        # Check for recent searches (within threshold hours)
        threshold_time = datetime.now(UTC) - timedelta(hours=hours_threshold)
        
        query = {
            "destination": destination.title(),
            "theme": theme,
            "hotel_rating": hotel_rating,
            "search_timestamp": {"$gte": threshold_time.isoformat()}
        }
        
        result = collection.find_one(query, sort=[("search_timestamp", -1)])
        
        if result:
            result['_id'] = str(result['_id'])
            logger.info(f"Found cached hotels & restaurants search for {destination}")
            return result
            
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving hotels & restaurants search: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving hotels & restaurants search: {e}")
        return None

async def get_hotels_restaurants_by_destination(destination: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get hotels and restaurants searches for a specific destination"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        query = {"destination": destination.title()}
        
        cursor = collection.find(
            query,
            {
                "destination": 1,
                "theme": 1,
                "hotel_rating": 1,
                "search_timestamp": 1,
                "hotels": 1,
                "restaurants": 1,
                "metadata.total_hotels": 1,
                "metadata.total_restaurants": 1
            }
        ).sort("search_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving hotels & restaurants by destination: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving hotels & restaurants by destination: {e}")
        return []

async def get_recent_hotels_restaurants_searches(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent hotels and restaurants searches for history"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        cursor = collection.find(
            {},
            {
                "destination": 1,
                "theme": 1,
                "activity_preferences": 1,
                "hotel_rating": 1,
                "search_timestamp": 1,
                "metadata.total_hotels": 1,
                "metadata.total_restaurants": 1
            }
        ).sort("search_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving hotels & restaurants history: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving hotels & restaurants history: {e}")
        return []

async def update_hotels_restaurants_search(search_id: str, update_data: Dict[str, Any]) -> bool:
    """Update an existing hotels and restaurants search record"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        # Add updated timestamp
        update_data["updated_timestamp"] = datetime.now(UTC).isoformat()
        
        result = collection.update_one(
            {"_id": search_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Hotels & restaurants search updated: {search_id}")
            return True
        else:
            logger.warning(f"No hotels & restaurants search found to update: {search_id}")
            return False
            
    except PyMongoError as e:
        logger.error(f"Database error updating hotels & restaurants search: {e}")
        return False
    except Exception as e:
        logger.error(f"Error updating hotels & restaurants search: {e}")
        return False

async def delete_hotels_restaurants_search(search_id: str) -> bool:
    """Delete a hotels and restaurants search record"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        result = collection.delete_one({"_id": search_id})
        
        if result.deleted_count > 0:
            logger.info(f"Hotels & restaurants search deleted: {search_id}")
            return True
        else:
            logger.warning(f"No hotels & restaurants search found to delete: {search_id}")
            return False
            
    except PyMongoError as e:
        logger.error(f"Database error deleting hotels & restaurants search: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting hotels & restaurants search: {e}")
        return False

async def delete_old_hotels_restaurants_searches(days_old: int = 30) -> int:
    """Delete hotels and restaurants searches older than specified days"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)
        
        result = collection.delete_many({
            "search_timestamp": {"$lt": cutoff_date.isoformat()}
        })
        
        logger.info(f"Deleted {result.deleted_count} old hotels & restaurants searches")
        return result.deleted_count
        
    except PyMongoError as e:
        logger.error(f"Database error deleting old hotels & restaurants searches: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error deleting old hotels & restaurants searches: {e}")
        return 0

async def get_hotels_restaurants_stats() -> Dict[str, Any]:
    """Get statistics about hotels and restaurants searches"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        total_searches = collection.count_documents({})
        
        # Get most popular destinations
        popular_destinations = list(collection.aggregate([
            {"$group": {"_id": "$destination", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]))
        
        # Get most popular themes
        popular_themes = list(collection.aggregate([
            {"$group": {"_id": "$theme", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]))
        
        # Get recent activity (last 7 days)
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        recent_searches = collection.count_documents({
            "search_timestamp": {"$gte": seven_days_ago.isoformat()}
        })
        
        return {
            "total_searches": total_searches,
            "popular_destinations": [{"destination": item["_id"], "count": item["count"]} for item in popular_destinations],
            "popular_themes": [{"theme": item["_id"], "count": item["count"]} for item in popular_themes],
            "recent_searches_7_days": recent_searches
        }
        
    except PyMongoError as e:
        logger.error(f"Database error getting hotels & restaurants stats: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error getting hotels & restaurants stats: {e}")
        return {}
    
async def get_search_history_by_destination(destination: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get search history for hotels and restaurants by destination"""
    try:
        db = get_db()
        collection = db.hotels_restaurants
        
        query = {"destination": destination.title()}
        
        cursor = collection.find(
            query,
            {
                "destination": 1,
                "theme": 1,
                "activity_preferences": 1,
                "hotel_rating": 1,
                "search_timestamp": 1,
                "search_results": 1,
                "agent_version": 1
            }
        ).sort("search_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        logger.info(f"Retrieved {len(results)} search history records for {destination}")
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving search history by destination: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving search history by destination: {e}")
        return []