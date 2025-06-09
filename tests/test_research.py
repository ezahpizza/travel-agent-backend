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

def test_research_validation(monkeypatch):
    # Patch to avoid DB or real API access
    class DummyService:
        async def research_destination(self, *args, **kwargs):
            return None
    class DummyCrud:
        async def get_research_by_destination(self, *args, **kwargs):
            return None
    monkeypatch.setattr("services.research_service.ResearchService", DummyService)
    monkeypatch.setattr("db.research_crud.get_research_by_destination", DummyCrud().get_research_by_destination)
    response = client.post("/research/destination", json={"destination": "BOM"})
    assert response.status_code == 422

# def test_research_success(monkeypatch):
#     class DummyService:
#         async def research_destination(self, *args, **kwargs):
#             return {"destination": "Rome", "research_summary": "summary", "attractions": [], "recommendations": [], "safety_tips": []}
#     class DummyCrud:
#         async def get_research_by_destination(self, *args, **kwargs):
#             return None
#         async def save_research_result(self, *args, **kwargs):
#             return "dummy_id"
#     monkeypatch.setattr("services.research_service.ResearchService", DummyService)
#     monkeypatch.setattr("db.research_crud.get_research_by_destination", DummyCrud().get_research_by_destination)
#     monkeypatch.setattr("db.research_crud.save_research_result", DummyCrud().save_research_result)
#     payload = {
#         "destination": "BOM",
#         "theme": "Culture",
#         "activities": "Museums",
#         "num_days": 3,
#         "budget": "Standard",
#         "flight_class": "Economy",
#         "hotel_rating": "Any",
#         "visa_required": False,
#         "insurance_required": False
#     }
#     response = client.post("/research/destination", json=payload)
#     assert response.status_code == 200
#     assert response.json()["success"] is True
#     assert response.json()["data"]["destination"] == "BOM"
