from fastapi import APIRouter, HTTPException, Depends
import logging
from datetime import datetime, UTC

from models.schemas import FlightSearchRequest, FlightSearchResponse, APIResponse
from services.flights_service import FlightService
from db.flights_crud import save_flight_search, get_flight_search_by_params

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/search", response_model=APIResponse)
async def search_flights(request: FlightSearchRequest):
    """
    Search for flights using SerpAPI and return top 3 cheapest options
    """
    try:
        logger.info(f"Searching flights from {request.source} to {request.destination}")
        
        # Check if we have recent cached results
        cached_results = await get_flight_search_by_params(
            request.source, 
            request.destination, 
            request.departure_date, 
            request.return_date
        )
        
        if cached_results:
            logger.info("Returning cached flight results")
            return APIResponse(
                success=True,
                message="Flight search completed (cached)",
                data=cached_results['processed_flights']
            )
        
        # Fetch new flight data
        flight_service = FlightService()
        flight_data = await flight_service.search_flights(
            request.source,
            request.destination,
            request.departure_date,
            request.return_date
        )
        
        if not flight_data or not flight_data.get('flights'):
            return APIResponse(
                success=False,
                message="No flights found for the specified criteria",
                data=[]
            )
        
        # Save to database
        search_record = {
            "source": request.source,
            "destination": request.destination,
            "departure_date": request.departure_date.isoformat(),
            "return_date": request.return_date.isoformat(),
            "raw_response": flight_data['raw_response'],
            "processed_flights": flight_data['flights'],
            "search_timestamp": datetime.now(UTC).isoformat(),
            "metadata": flight_data.get('metadata', {})
        }
        
        await save_flight_search(search_record)
        
        return APIResponse(
            success=True,
            message=f"Found {len(flight_data['flights'])} flights",
            data=flight_data['flights']
        )
        
    except Exception as e:
        logger.error(f"Flight search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")

@router.get("/search/history")
async def get_search_history(limit: int = 10):
    """
    Get recent flight search history
    """
    try:
        from db.flights_crud import get_recent_flight_searches
        
        history = await get_recent_flight_searches(limit)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(history)} search records",
            data=history
        )
        
    except Exception as e:
        logger.error(f"Error retrieving search history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search history")