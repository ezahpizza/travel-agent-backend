import sys
import os
os.environ["ENV"] = "test"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

import db.connection

class DummyDB:
    def __getattr__(self, name):
        async def dummy(*args, **kwargs):
            return None
        return dummy

def test_generate_itinerary_validation():
    # Missing required fields
    response = client.post("/itinerary/generate", json={"destination": "BOM"})
    assert response.status_code == 422

def test_generate_itinerary_success(monkeypatch):
    # Patch the service to avoid real API calls
    class DummyService:
        async def generate_itinerary(self, **kwargs):
            return {"dummy": "itinerary"}
    class DummyCrud:
        async def save_itinerary(self, itinerary_data):
            return "dummy_id"
        async def get_itineraries_by_params(self, *args, **kwargs):
            return None
    monkeypatch.setattr("services.itinerary_service.ItineraryService", DummyService)
    monkeypatch.setattr("db.itinerary_crud.save_itinerary", DummyCrud().save_itinerary)
    monkeypatch.setattr("db.itinerary_crud.get_itineraries_by_params", DummyCrud().get_itineraries_by_params)
    # Patch the router import if needed
    import routers.itinerary
    routers.itinerary.save_itinerary = DummyCrud().save_itinerary
    routers.itinerary.get_itineraries_by_params = DummyCrud().get_itineraries_by_params
    payload = {
        "destination": "BOM",
        "theme": "Romantic",
        "activities": "Sightseeing",
        "num_days": 3,
        "budget": "Standard",
        "flight_class": "Economy",
        "hotel_rating": "Any",
        "visa_required": False,
        "insurance_required": False,
        "userid": "test-user"
    }
    response = client.post("/itinerary/generate", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_get_itineraries_by_destination(monkeypatch):
    class DummyCrud:
        async def get_itineraries_by_destination(self, destination, limit):
            return [{"destination": destination, "theme": "Test", "num_days": 1}]
    monkeypatch.setattr("db.itinerary_crud.get_itineraries_by_destination", DummyCrud().get_itineraries_by_destination)
    response = client.get("/itinerary/destination/Paris?limit=1")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]) == 1
