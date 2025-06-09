import os
import logging
from datetime import date
from typing import Dict, List, Any, Optional
from serpapi import GoogleSearch

from utils.date_utils import format_datetime

logger = logging.getLogger(__name__)

class FlightService:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable is required")

    async def search_flights(self, source: str, destination: str, departure_date: date, return_date: date) -> Dict[str, Any]:
        """
        Search for flights using SerpAPI and return processed results
        """
        try:
            params = {
                "engine": "google_flights",
                "departure_id": source.upper(),
                "arrival_id": destination.upper(),
                "outbound_date": departure_date.strftime("%Y-%m-%d"),
                "return_date": return_date.strftime("%Y-%m-%d"),
                "currency": "INR",
                "hl": "en",
                "api_key": self.api_key
            }
            
            logger.info(f"Searching flights with params: {params}")
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if not results or "best_flights" not in results:
                logger.warning("No flight data in API response")
                return {"flights": [], "raw_response": results, "metadata": {}}
            
            # Extract and process flights
            processed_flights = self._extract_cheapest_flights(results.get("best_flights", []))
            
            return {
                "flights": processed_flights,
                "raw_response": results,
                "metadata": {
                    "search_params": params,
                    "total_results": len(results.get("best_flights", [])),
                    "processed_count": len(processed_flights)
                }
            }
            
        except Exception as e:
            logger.error(f"Flight search error: {str(e)}")
            raise

    def _extract_cheapest_flights(self, flight_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract and format the top 3 cheapest flights
        """
        try:
            if not flight_data:
                return []
            
            # Sort by price, handling missing prices
            sorted_flights = sorted(
                flight_data,
                key=lambda x: self._extract_price_value(x.get("price", ""))
            )[:3]
            
            processed_flights = []
            for flight in sorted_flights:
                processed_flight = self._format_flight_data(flight)
                if processed_flight:
                    processed_flights.append(processed_flight)
            
            return processed_flights
            
        except Exception as e:
            logger.error(f"Error processing flight data: {str(e)}")
            return []

    def _format_flight_data(self, flight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Format individual flight data for response
        """
        try:
            flights_info = flight.get("flights", [{}])
            if not flights_info:
                return None
                
            departure_info = flights_info[0].get("departure_airport", {})
            arrival_info = flights_info[-1].get("arrival_airport", {})
            
            return {
                "airline": flights_info[0].get("airline", "Unknown Airline"),
                "airline_logo": flight.get("airline_logo", ""),
                "price": str(flight.get("price", "Not Available")),
                "total_duration": str(flight.get("total_duration", "N/A")),
                "departure_time": format_datetime(departure_info.get("time", "")),
                "arrival_time": format_datetime(arrival_info.get("time", "")),
                "departure_airport": departure_info.get("name", ""),
                "arrival_airport": arrival_info.get("name", ""),
                "booking_token": flight.get("booking_token", ""),
                "departure_token": flight.get("departure_token", ""),
                "flight_details": flights_info
            }
            
        except Exception as e:
            logger.error(f"Error formatting flight data: {str(e)}")
            return None

    def _extract_price_value(self, price_str: str) -> float:
        """
        Extract numeric price value for sorting
        """
        try:
            if not price_str or price_str == "Not Available":
                return float('inf')
            
            # Remove currency symbols and commas, extract numbers
            import re
            numbers = re.findall(r'[\d,]+', str(price_str))
            if numbers:
                return float(numbers[0].replace(',', ''))
            return float('inf')
            
        except (ValueError, IndexError):
            return float('inf')

    async def get_booking_link(self, booking_token: str, departure_token: str) -> str:
        """
        Generate booking link using tokens
        """
        try:
            if not booking_token:
                return "#"
            
            base_url = "https://www.google.com/travel/flights"
            return f"{base_url}?tfs={booking_token}"
            
        except Exception as e:
            logger.error(f"Error generating booking link: {str(e)}")
            return "#"