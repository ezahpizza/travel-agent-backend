from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime, UTC

from models.schemas import ItineraryRequest, ItineraryResponse, APIResponse
from services.itinerary_service import ItineraryService
from db.itinerary_crud import save_itinerary, get_itineraries_by_params

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=APIResponse)
async def generate_itinerary(request: ItineraryRequest):
    """
    Generate a complete travel itinerary using Gemini agent
    """
    try:
        logger.info(f"Generating itinerary for {request.destination} - {request.num_days} days")
        
        # Check for similar cached itinerary
        cached_itinerary = await get_itineraries_by_params(
            request.destination,
            request.theme,
            request.num_days,
            hours_threshold=24
        )
        
        if cached_itinerary:
            logger.info("Returning cached itinerary")
            return APIResponse(
                success=True,
                message="Itinerary generated (cached)",
                data=cached_itinerary['itinerary_data']
            )
        
        # Generate new itinerary
        itinerary_service = ItineraryService()
        itinerary_data = await itinerary_service.generate_itinerary(
            destination=request.destination,
            theme=request.theme,
            activities=request.activities,
            num_days=request.num_days,
            budget=request.budget.value if hasattr(request.budget, "value") else str(request.budget),
            flight_class=request.flight_class.value if hasattr(request.flight_class, "value") else str(request.flight_class),
            hotel_rating=request.hotel_rating.value if hasattr(request.hotel_rating, "value") else str(request.hotel_rating),
            visa_required=request.visa_required,
            insurance_required=request.insurance_required,
            research_summary=request.research_summary,
            selected_flights=request.selected_flights,
            hotel_restaurant_summary=request.hotel_restaurant_summary
        )
        
        if not itinerary_data:
            return APIResponse(
                success=False,
                message="Failed to generate itinerary",
                data=None
            )
        
        # Save to database
        itinerary_record = {
            "destination": request.destination,
            "theme": request.theme,
            "activities": request.activities,
            "num_days": request.num_days,
            "budget": request.budget,
            "flight_class": request.flight_class,
            "hotel_rating": request.hotel_rating,
            "visa_required": request.visa_required,
            "insurance_required": request.insurance_required,
            "research_summary": request.research_summary,
            "selected_flights": request.selected_flights,
            "hotel_restaurant_summary": request.hotel_restaurant_summary,
            "itinerary_data": itinerary_data,
            "timestamp": datetime.now(UTC).isoformat(),
            "agent_version": "gemini-2.5-flash-preview-04-17"
        }
        
        await save_itinerary(itinerary_record)
        
        return APIResponse(
            success=True,
            message=f"Generated {request.num_days}-day itinerary for {request.destination}",
            data=itinerary_data
        )
        
    except Exception as e:
        logger.error(f"Itinerary generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Itinerary generation failed: {str(e)}")

@router.get("/destination/{destination}")
async def get_itineraries_by_destination(destination: str, limit: int = 10, offset: int = 0):
    """
    Get itineraries for a specific destination with pagination
    """
    try:
        from db.itinerary_crud import get_itineraries_by_destination
        itineraries = await get_itineraries_by_destination(destination, limit+offset)
        paginated = itineraries[offset:offset+limit]
        return APIResponse(
            success=True,
            message=f"Retrieved {len(paginated)} itineraries for {destination}",
            data=paginated
        )
    except Exception as e:
        import traceback
        logger.error(f"Error retrieving itineraries: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to retrieve itineraries")

@router.get("/{itinerary_id}")
async def get_itinerary_by_id(itinerary_id: str):
    """
    Get specific itinerary by ID
    """
    try:
        from db.itinerary_crud import get_itinerary_by_id
        
        itinerary = await get_itinerary_by_id(itinerary_id)
        
        if not itinerary:
            raise HTTPException(status_code=404, detail="Itinerary not found")
        
        return APIResponse(
            success=True,
            message="Itinerary retrieved successfully",
            data=itinerary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve itinerary")