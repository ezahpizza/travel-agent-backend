import sys
import os
os.environ["ENV"] = "test"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app
import db.connection

client = TestClient(app)

class DummyDB:
    def __getattr__(self, name):
        async def dummy(*args, **kwargs):
            return None
        return dummy

def test_search_flights_validation():
    response = client.post("/flights/search", json={"source": "DEL"})
    assert response.status_code == 422

# def test_search_flights_success(monkeypatch):
#     class DummyService:
#         async def search_flights(self, **kwargs):
#             return {"flights": [], "search_metadata": {}}
#     class DummyCrud:
#         async def save_flight_search(self, search_data):
#             return "dummy_id"
#         async def get_flight_search_by_params(self, *args, **kwargs):
#             return None
#     monkeypatch.setattr("services.flights_service.FlightService", DummyService)
#     monkeypatch.setattr("db.flights_crud.save_flight_search", DummyCrud().save_flight_search)
#     monkeypatch.setattr("db.flights_crud.get_flight_search_by_params", DummyCrud().get_flight_search_by_params)
#     payload = {
#         "source": "DEL",
#         "destination": "BOM",
#         "departure_date": "2025-07-01",
#         "return_date": "2025-07-10"
#     }
#     response = client.post("/flights/search", json=payload)
#     assert response.status_code == 200
#     assert response.json()["success"] is True
#     assert "flights" in response.json()["data"]
