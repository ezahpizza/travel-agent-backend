from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

class BudgetType(str, Enum):
    ECONOMY = "Economy"
    STANDARD = "Standard"
    LUXURY = "Luxury"

class FlightClass(str, Enum):
    ECONOMY = "Economy"
    BUSINESS = "Business"
    FIRST_CLASS = "First Class"

class HotelRating(str, Enum):
    ANY = "Any"
    THREE_STAR = "3⭐"
    FOUR_STAR = "4⭐"
    FIVE_STAR = "5⭐"

# Flight Models
class FlightSearchRequest(BaseModel):
    source: str = Field(..., description="Departure airport IATA code", min_length=3, max_length=3)
    destination: str = Field(..., description="Arrival airport IATA code", min_length=3, max_length=3)
    departure_date: date = Field(..., description="Departure date")
    return_date: date = Field(..., description="Return date")
    
    @field_validator('source', 'destination')
    @classmethod
    def validate_iata_code(cls, v):
        return v.upper()
    
    @field_validator('return_date')
    @classmethod
    def validate_return_date(cls, v, values):
        if values.data.get('departure_date') and v <= values.data['departure_date']:
            raise ValueError('Return date must be after departure date')
        return v

class FlightInfo(BaseModel):
    airline: str
    airline_logo: Optional[str] = None
    price: str
    total_duration: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    booking_token: Optional[str] = None

class FlightSearchResponse(BaseModel):
    flights: List[FlightInfo]
    search_metadata: Dict[str, Any]

# Research Models
class ResearchRequest(BaseModel):
    destination: str = Field(..., description="Destination city/country")
    theme: str = Field(..., description="Travel theme")
    activities: str = Field(..., description="Preferred activities")
    num_days: int = Field(..., ge=1, le=30, description="Trip duration in days")
    budget: BudgetType
    flight_class: FlightClass
    hotel_rating: HotelRating
    visa_required: bool = False
    insurance_required: bool = False

class ResearchResponse(BaseModel):
    destination: str
    research_summary: str
    attractions: List[str]
    recommendations: List[str]
    safety_tips: List[str]

# Hotels & Restaurants Models
class HotelRestaurantRequest(BaseModel):
    destination: str = Field(..., description="Destination city/country")
    theme: str = Field(..., description="Travel theme")
    activity_preferences: str = Field(..., description="Activity preferences")
    hotel_rating: HotelRating
    budget: str

class HotelInfo(BaseModel):
    name: str
    address: Optional[str] = None
    price_range: Optional[str] = None
    rating: Optional[float] = None
    description: Optional[str] = None

class RestaurantInfo(BaseModel):
    name: str
    address: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    rating: Optional[float] = None
    description: Optional[str] = None

# Itinerary Models
class ItineraryRequest(BaseModel):
    destination: str = Field(..., description="Destination city/country")
    theme: str = Field(..., description="Travel theme")
    activities: str = Field(..., description="Preferred activities")
    num_days: int = Field(..., ge=1, le=30, description="Trip duration in days")
    budget: BudgetType
    flight_class: FlightClass
    hotel_rating: HotelRating
    visa_required: bool = False
    insurance_required: bool = False
    research_summary: str
    selected_flights: List[Dict[str, Any]]
    hotel_restaurant_summary: str

class DayActivity(BaseModel):
    time: str
    activity: str
    location: Optional[str] = None
    duration: Optional[str] = None
    cost_estimate: Optional[str] = None
    notes: Optional[str] = None

class DayPlan(BaseModel):
    day: int
    date: Optional[str] = None
    theme: str
    activities: List[DayActivity]
    estimated_cost: Optional[str] = None

class ItineraryResponse(BaseModel):
    destination: str
    total_days: int
    theme: str
    daily_plans: List[DayPlan]
    total_estimated_cost: Optional[str] = None
    travel_tips: List[str]
    packing_suggestions: List[str]

# Generic API Response
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None