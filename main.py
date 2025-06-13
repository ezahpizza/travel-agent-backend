from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routers import flights, research, hotels_restaurants, itinerary
from db.connection import init_db, close_db

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
    lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(flights.router, prefix="/flights", tags=["flights"])
app.include_router(research.router, prefix="/research", tags=["research"])
app.include_router(hotels_restaurants.router, prefix="/hotels-restaurants", tags=["hotels-restaurants"])
app.include_router(itinerary.router, prefix="/itinerary", tags=["itinerary"])

@app.get("/")
async def root():
    return {"message": "AI Travel Planner API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)