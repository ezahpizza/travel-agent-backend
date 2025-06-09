import logging
from datetime import datetime, timedelta, UTC
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

async def get_research_by_id(research_id: str) -> Optional[Dict[str, Any]]:
    """Get research by ID"""
    try:
        db = get_db()
        collection = db.research
        
        result = collection.find_one({"_id": research_id})
        
        if result:
            result['_id'] = str(result['_id'])
            logger.info(f"Retrieved research: {research_id}")
            return result
            
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving research: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving research: {e}")
        return None

async def get_research_by_params(destination: str, theme: str, num_days: int,
                               hours_threshold: int = 12) -> Optional[Dict[str, Any]]:
    """Get cached research if recent enough"""
    try:
        db = get_db()
        collection = db.research
        
        threshold_time = datetime.now(UTC) - timedelta(hours=hours_threshold)
        
        query = {
            "destination": destination.title(),
            "theme": theme,
            "num_days": num_days,
            "created_timestamp": {"$gte": threshold_time.isoformat()}
        }
        
        result = collection.find_one(query, sort=[("created_timestamp", -1)])
        
        if result:
            result['_id'] = str(result['_id'])
            logger.info(f"Found cached research for {destination}")
            return result
            
        return None
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving cached research: {e}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving cached research: {e}")
        return None

async def get_research_by_destination(destination: str, theme: str ,limit: int = 10) -> List[Dict[str, Any]]:
    """Get research for a specific destination"""
    try:
        db = get_db()
        collection = db.research
        
        query = {"destination": destination.title()}
        
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
        logger.error(f"Database error retrieving research by destination: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving research by destination: {e}")
        return []

async def get_recent_research(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent research records"""
    try:
        db = get_db()
        collection = db.research
        
        cursor = collection.find(
            {},
            {
                "destination": 1,
                "theme": 1,
                "num_days": 1,
                "budget": 1,
                "activities": 1,
                "created_timestamp": 1,
                "visa_required": 1,
                "insurance_required": 1
            }
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving recent research: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving recent research: {e}")
        return []

async def update_research(research_id: str, update_data: Dict[str, Any]) -> bool:
    """Update existing research"""
    try:
        db = get_db()
        collection = db.research
        
        update_data["updated_timestamp"] = datetime.now(UTC).isoformat()
        
        result = collection.update_one(
            {"_id": research_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"Research updated: {research_id}")
            return True
        else:
            logger.warning(f"No research found to update: {research_id}")
            return False
            
    except PyMongoError as e:
        logger.error(f"Database error updating research: {e}")
        return False
    except Exception as e:
        logger.error(f"Error updating research: {e}")
        return False

async def delete_research(research_id: str) -> bool:
    """Delete research record"""
    try:
        db = get_db()
        collection = db.research
        
        result = collection.delete_one({"_id": research_id})
        
        if result.deleted_count > 0:
            logger.info(f"Research deleted: {research_id}")
            return True
        else:
            logger.warning(f"No research found to delete: {research_id}")
            return False
            
    except PyMongoError as e:
        logger.error(f"Database error deleting research: {e}")
        return False
    except Exception as e:
        logger.error(f"Error deleting research: {e}")
        return False

async def search_research_by_activities(activities: List[str], limit: int = 20) -> List[Dict[str, Any]]:
    """Search research by activity preferences"""
    try:
        db = get_db()
        collection = db.research
        
        # Create text search query for activities
        activity_regex = "|".join(activities)
        
        query = {
            "$or": [
                {"activities": {"$regex": activity_regex, "$options": "i"}},
                {"research_summary": {"$regex": activity_regex, "$options": "i"}},
                {"attractions": {"$regex": activity_regex, "$options": "i"}}
            ]
        }
        
        cursor = collection.find(
            query,
            {
                "destination": 1,
                "theme": 1,
                "activities": 1,
                "research_summary": 1,
                "attractions": 1,
                "created_timestamp": 1
            }
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error searching research by activities: {e}")
        return []
    except Exception as e:
        logger.error(f"Error searching research by activities: {e}")
        return []

async def get_research_by_theme(theme: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Get research filtered by travel theme"""
    try:
        db = get_db()
        collection = db.research
        
        query = {"theme": theme}
        
        cursor = collection.find(
            query,
            {
                "destination": 1,
                "theme": 1,
                "num_days": 1,
                "budget": 1,
                "research_summary": 1,
                "created_timestamp": 1
            }
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving research by theme: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving research by theme: {e}")
        return []

async def delete_old_research(days_old: int = 60) -> int:
    """Delete research older than specified days"""
    try:
        db = get_db()
        collection = db.research
        
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)
        
        result = collection.delete_many({
            "created_timestamp": {"$lt": cutoff_date.isoformat()}
        })
        
        logger.info(f"Deleted {result.deleted_count} old research records")
        return result.deleted_count
        
    except PyMongoError as e:
        logger.error(f"Database error deleting old research: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error deleting old research: {e}")
        return 0

async def get_research_stats() -> Dict[str, Any]:
    """Get research statistics"""
    try:
        db = get_db()
        collection = db.research
        
        total_research = collection.count_documents({})
        
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
        
        # Visa requirements stats
        visa_stats = list(collection.aggregate([
            {"$group": {"_id": "$visa_required", "count": {"$sum": 1}}}
        ]))
        
        # Recent activity
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)
        recent_research = collection.count_documents({
            "created_timestamp": {"$gte": seven_days_ago.isoformat()}
        })
        
        return {
            "total_research": total_research,
            "popular_destinations": [{"destination": item["_id"], "count": item["count"]} for item in popular_destinations],
            "popular_themes": [{"theme": item["_id"], "count": item["count"]} for item in popular_themes],
            "visa_requirements": {str(item["_id"]): item["count"] for item in visa_stats},
            "recent_research_7_days": recent_research
        }
        
    except PyMongoError as e:
        logger.error(f"Database error getting research stats: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error getting research stats: {e}")
        return {}
    
async def save_research_result(research_data: Dict[str, Any]) -> str:
    """Save research result to MongoDB (alias for save_research)"""
    return await save_research(research_data)

async def get_research_by_destination_and_theme(destination: str, theme: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get research for specific destination and theme combination"""
    try:
        db = get_db()
        collection = db.research
        
        query = {
            "destination": destination.title(),
            "theme": theme
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
                "cultural_info": 1,
                "safety_tips": 1,
                "visa_required": 1,
                "insurance_required": 1
            }
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving research by destination and theme: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving research by destination and theme: {e}")
        return []

async def search_research_by_keywords(keywords: List[str], limit: int = 20) -> List[Dict[str, Any]]:
    """Search research by keywords across multiple fields"""
    try:
        db = get_db()
        collection = db.research
        
        # Create regex pattern for keywords
        keyword_patterns = [{"$regex": keyword, "$options": "i"} for keyword in keywords]
        
        query = {
            "$or": [
                {"destination": {"$in": keyword_patterns}},
                {"theme": {"$in": keyword_patterns}},
                {"activities": {"$in": keyword_patterns}},
                {"research_summary": {"$in": keyword_patterns}},
                {"attractions": {"$in": keyword_patterns}}
            ]
        }
        
        cursor = collection.find(
            query,
            {
                "destination": 1,
                "theme": 1,
                "activities": 1,
                "research_summary": 1,
                "attractions": 1,
                "created_timestamp": 1,
                "visa_required": 1,
                "insurance_required": 1
            }
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error searching research by keywords: {e}")
        return []
    except Exception as e:
        logger.error(f"Error searching research by keywords: {e}")
        return []

async def get_research_by_budget(budget: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Get research filtered by budget level"""
    try:
        db = get_db()
        collection = db.research
        
        query = {"budget": budget}
        
        cursor = collection.find(
            query,
            {
                "destination": 1,
                "theme": 1,
                "num_days": 1,
                "budget": 1,
                "research_summary": 1,
                "created_timestamp": 1,
                "attractions": 1
            }
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving research by budget: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving research by budget: {e}")
        return []

async def get_research_with_visa_info(visa_required: bool = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Get research filtered by visa requirements"""
    try:
        db = get_db()
        collection = db.research
        
        query = {}
        if visa_required is not None:
            query["visa_required"] = visa_required
            
        cursor = collection.find(
            query,
            {
                "destination": 1,
                "theme": 1,
                "visa_required": 1,
                "insurance_required": 1,
                "research_summary": 1,
                "created_timestamp": 1
            }
        ).sort("created_timestamp", -1).limit(limit)
        
        results = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            results.append(doc)
            
        return results
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving research with visa info: {e}")
        return []
    except Exception as e:
        logger.error(f"Error retrieving research with visa info: {e}")
        return []

async def count_research_by_destination(destination: str) -> int:
    """Count research records for a specific destination"""
    try:
        db = get_db()
        collection = db.research
        
        count = collection.count_documents({"destination": destination.title()})
        return count
        
    except PyMongoError as e:
        logger.error(f"Database error counting research by destination: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error counting research by destination: {e}")
        return 0

async def get_research_summary_stats() -> Dict[str, Any]:
    """Get enhanced research statistics with more details"""
    try:
        db = get_db()
        collection = db.research
        
        # Basic stats
        total_research = collection.count_documents({})
        
        # Most researched destinations (top 10)
        top_destinations = list(collection.aggregate([
            {"$group": {"_id": "$destination", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]))
        
        # Popular themes
        popular_themes = list(collection.aggregate([
            {"$group": {"_id": "$theme", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 8}
        ]))
        
        # Budget distribution
        budget_distribution = list(collection.aggregate([
            {"$group": {"_id": "$budget", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))
        
        # Average trip duration by theme
        avg_duration_by_theme = list(collection.aggregate([
            {"$group": {
                "_id": "$theme", 
                "avg_days": {"$avg": "$num_days"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]))
        
        # Visa requirement stats
        visa_stats = list(collection.aggregate([
            {"$group": {"_id": "$visa_required", "count": {"$sum": 1}}}
        ]))
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        recent_research = collection.count_documents({
            "created_timestamp": {"$gte": thirty_days_ago.isoformat()}
        })
        
        return {
            "total_research": total_research,
            "top_destinations": [{"destination": item["_id"], "count": item["count"]} for item in top_destinations],
            "popular_themes": [{"theme": item["_id"], "count": item["count"]} for item in popular_themes],
            "budget_distribution": [{"budget": item["_id"], "count": item["count"]} for item in budget_distribution],
            "avg_duration_by_theme": [
                {
                    "theme": item["_id"], 
                    "avg_days": round(item["avg_days"], 1),
                    "count": item["count"]
                } for item in avg_duration_by_theme
            ],
            "visa_requirements": {str(item["_id"]): item["count"] for item in visa_stats},
            "recent_research_30_days": recent_research
        }
        
    except PyMongoError as e:
        logger.error(f"Database error getting enhanced research stats: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error getting enhanced research stats: {e}")
        return {}