from fastapi import APIRouter, HTTPException, Query
import logging
from datetime import datetime, UTC

from models.schemas import HotelRestaurantRequest, APIResponse
from services.hotels_restaurants_service import HotelsRestaurantsService
from db.hotels_restaurants_crud import (
    save_hotels_restaurants_search, 
    get_hotels_restaurants_by_params,
    get_search_history_by_destination  
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/search", response_model=APIResponse)
async def search_hotels_restaurants(request: HotelRestaurantRequest):
    """
    Search for hotels and restaurants using Gemini agent and SerpAPI
    """
    try:
        logger.info(f"Searching hotels and restaurants for {request.destination} for user {request.userid}")
        
        # Check for cached results
        cached_results = await get_hotels_restaurants_by_params(
            request.destination,
            request.theme,
            request.hotel_rating,
            request.userid
        )
        
        if cached_results:
            logger.info(f"Returning cached hotel/restaurant results for user {request.userid}")
            return APIResponse(
                success=True,
                message="Search completed (cached)",
                data=cached_results['search_results']
            )
        
        # Perform new search
        service = HotelsRestaurantsService()
        search_results = await service.search_hotels_restaurants(
            destination=request.destination,
            theme=request.theme,
            activity_preferences=request.activity_preferences,
            hotel_rating=request.hotel_rating.value if hasattr(request.hotel_rating, "value") else str(request.hotel_rating),
            budget=request.budget 
        )
        
        if not search_results:
            return APIResponse(
                success=False,
                message="No hotels or restaurants found",
                data={"hotels": [], "restaurants": []}
            )
        
        # Save to database
        search_record = {
            "destination": request.destination,
            "theme": request.theme,
            "activity_preferences": request.activity_preferences,
            "hotel_rating": request.hotel_rating,
            "userid": request.userid,
            "search_results": search_results,
            "timestamp": datetime.now(UTC).isoformat(),
            "agent_version": "gemini-2.5-flash-preview-04-17"
        }
        
        await save_hotels_restaurants_search(search_record)
        
        return APIResponse(
            success=True,
            message="Hotels and restaurants search completed",
            data=search_results
        )
        
    except Exception as e:
        logger.error(f"Hotel/restaurant search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
@router.get("/destination/{destination}/history")
async def get_search_history(
    destination: str, 
    userid: str = Query(..., description="User ID from Clerk authentication"),
    limit: int = Query(5, ge=1, le=50, description="Number of records to return")
):
    """
    Get search history for hotels and restaurants by destination
    """
    try:        
        history = await get_search_history_by_destination(destination, userid, limit)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(history)} search records for {destination}",
            data=history
        )
        
    except Exception as e:
        logger.error(f"Error retrieving search history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search history")