#standard library imports
import os
from contextlib import asynccontextmanager

# Third-party imports
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local application imports
from config import settings
from db.connection import init_db, close_db
from routers import flights, research, hotels_restaurants, itinerary, subscription

# Load environment variables
load_dotenv()

# Initialize database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("ENV") != "test":
        await init_db()
    yield
    if os.environ.get("ENV") != "test":
        close_db()

app = FastAPI(    
    title="AI Travel Planner API",
    description="Production-ready FastAPI backend for AI-powered travel planning",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS] if settings.CORS_ORIGINS else ["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(flights.router, prefix="/flights", tags=["flights"])
app.include_router(research.router, prefix="/research", tags=["research"])
app.include_router(hotels_restaurants.router, prefix="/hotels-restaurants", tags=["hotels-restaurants"])
app.include_router(itinerary.router, prefix="/itinerary", tags=["itinerary"])
app.include_router(subscription.router, prefix="/subscription", tags=["subscription"])

@app.get("/")
async def root():
    return {"message": "AI Travel Planner API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)