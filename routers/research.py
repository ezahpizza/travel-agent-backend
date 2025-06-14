# Standard Library Imports
import logging
from datetime import datetime, UTC

# Third-PartyImports
from fastapi import APIRouter, HTTPException

# Application-Specific Imports
from models.schemas import ResearchRequest, APIResponse
from services.research_service import ResearchService
from db.research_crud import (
    save_research_result,
    get_research_by_destination,
    get_research_history_by_destination,
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/destination", response_model=APIResponse)
async def research_destination(request: ResearchRequest):
    """
    Research destination using Gemini agent and SerpAPI tools
    """
    try:
        logger.info(f"Researching destination: {request.destination}")
        
        # Check for recent cached research
        cached_research = await get_research_by_destination(
            request.destination, 
            request.theme, 
            request.num_days
        )
        
        if cached_research:
            logger.info("Returning cached research results")
            return APIResponse(
                success=True,
                message="Research completed (cached)",
                data=cached_research['research_data']
            )
        
        # Perform new research
        research_service = ResearchService()
        research_data = await research_service.research_destination(request)
        
        if not research_data:
            return APIResponse(
                success=False,
                message="Failed to generate research for destination",
                data=None
            )
        
        # Save to database
        research_record = {
            "destination": request.destination,
            "theme": request.theme,
            "activities": request.activities,
            "num_days": request.num_days,
            "budget": request.budget,
            "flight_class": request.flight_class,
            "hotel_rating": request.hotel_rating,
            "visa_required": request.visa_required,
            "insurance_required": request.insurance_required,
            "research_data": research_data,
            "timestamp": datetime.now(UTC).isoformat(),
            "agent_version": "gemini-2.5-flash-preview-04-17"
        }
        
        await save_research_result(research_record)
        
        return APIResponse(
            success=True,
            message="Destination research completed successfully",
            data=research_data
        )
        
    except Exception as e:
        logger.error(f"Research error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@router.get("/destination/{destination}/history")
async def get_research_history(destination: str, limit: int = 5):
    """
    Get research history for a specific destination
    """
    try:
        history = await get_research_history_by_destination(destination, limit)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(history)} research records for {destination}",
            data=history
        )
        
    except Exception as e:
        logger.error(f"Error retrieving research history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve research history")