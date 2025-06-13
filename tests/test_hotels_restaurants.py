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

def test_search_hotels_restaurants_validation():
    # Missing required fields
    response = client.post("/hotels-restaurants/search", json={"destination": "BOM"})
    assert response.status_code == 422

# def test_search_hotels_restaurants_success(monkeypatch):
#     class DummyService:
#         async def search_hotels_restaurants(self, **kwargs):
#             return {"hotels": [], "restaurants": []}
#     class DummyCrud:
#         async def save_hotels_restaurants_search(self, search_data):
#             return "dummy_id"
#         async def get_hotels_restaurants_by_params(self, *args, **kwargs):
#             return None
#     monkeypatch.setattr("services.hotels_restaurants_service.HotelsRestaurantsService", DummyService)
#     monkeypatch.setattr("db.hotels_restaurants_crud.save_hotels_restaurants_search", DummyCrud().save_hotels_restaurants_search)
#     monkeypatch.setattr("db.hotels_restaurants_crud.get_hotels_restaurants_by_params", DummyCrud().get_hotels_restaurants_by_params)
#     payload = {
#         "destination": "BOM",
#         "theme": "Romantic",
#         "activity_preferences": "Sightseeing",
#         "hotel_rating": "Any",
#         "budget": "Standard",
#         "userid": "test-user"
#     }
#     response = client.post("/hotels-restaurants/search", json=payload)
#     assert response.status_code == 200
#     assert response.json()["success"] is True

# def test_get_hotels_restaurants_history(monkeypatch):
#     class DummyCrud:
#         async def get_hotels_restaurants_by_destination(self, destination, limit):
#             return [{"destination": destination, "theme": "Test"}]
#     monkeypatch.setattr("db.hotels_restaurants_crud.get_hotels_restaurants_by_destination", DummyCrud().get_hotels_restaurants_by_destination)
#     # Patch the router import if needed
#     import routers.hotels_restaurants
#     routers.hotels_restaurants.get_search_history_by_destination = DummyCrud().get_hotels_restaurants_by_destination
#     response = client.get("/hotels-restaurants/destination/Paris/history?limit=1")
#     assert response.status_code == 200
#     assert response.json()["success"] is True
#     assert len(response.json()["data"]) == 1
