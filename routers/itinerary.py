# Standard Library Imports
import logging
from datetime import datetime, UTC

# Third-Party Imports
from fastapi import APIRouter, HTTPException, Query, Depends

# Application-Specific Imports
from dependencies.paywall import paywall_dependency
from models.schemas import ItineraryRequest, APIResponse
from services.itinerary_service import ItineraryService
from db.itinerary_crud import (
    save_itinerary,
    get_itineraries_by_params,
    get_recent_itineraries_by_user,
    get_itinerary_by_id,
    delete_itinerary,
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=APIResponse, dependencies=[Depends(paywall_dependency)])
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
            request.userid,
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
            "userid": request.userid,  # Add this line
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

@router.get("/history")
async def get_user_itinerary_history(
    userid: str = Query(..., description="User ID from Clerk authentication"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return")
):
    """
    Get recent itinerary history for a specific user
    """
    try:
        history = await get_recent_itineraries_by_user(userid, limit)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(history)} itinerary records for user {userid}",
            data=history
        )
        
    except Exception as e:
        logger.error(f"Error retrieving itinerary history for user {userid}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve itinerary history")
    
@router.get("/{itinerary_id}")
async def get_itinerary_by_id(
    itinerary_id: str,
    userid: str = Query(..., description="User ID from Clerk authentication")
):
    """
    Get a specific itinerary by its ID
    """
    try:
        
        itinerary = await get_itinerary_by_id(itinerary_id, userid)
        
        if not itinerary:
            raise HTTPException(
                status_code=404, 
                detail="Itinerary not found or access denied"
            )
        
        return APIResponse(
            success=True,
            message=f"Retrieved itinerary {itinerary_id}",
            data=itinerary['itinerary_data']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving itinerary {itinerary_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve itinerary")
    

@router.delete("/{itinerary_id}")
async def delete_itinerary_endpoint(
    itinerary_id: str,
    userid: str = Query(..., description="User ID from Clerk authentication")
):
    """Delete a specific itinerary"""
    try:
        
        success = await delete_itinerary(itinerary_id, userid)
        
        if success:
            return APIResponse(
                success=True,
                message=f"Itinerary {itinerary_id} deleted successfully",
                data=None
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Itinerary not found or access denied"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting itinerary {itinerary_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete itinerary")