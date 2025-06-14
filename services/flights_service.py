# Standard Library Imports
import re
import logging
from datetime import date, datetime, UTC
from typing import Dict, List, Any, Optional

# Third-Party Imports
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini

# Application-Specific Imports
from config import settings

logger = logging.getLogger(__name__)

class FlightService:
    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        self.serpapi_key = settings.SERPAPI_API_KEY
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        if not self.serpapi_key:
            raise ValueError("SERPAPI_API_KEY environment variable is required")
        
        # Initialize the Gemini agent
        self.agent = Agent(
            name="Flight Search Assistant",
            instructions=[
                "Search for the best flight options between specified airports",
                "Find flights for both outbound and return dates",
                "Focus on finding the most affordable options while considering convenience",
                "For each flight, include: airline name, price, departure/arrival times, duration, and booking information",
                "Sort results by price (cheapest first) and provide top 3-5 options",
                "Include both direct and connecting flights when available",
                "Consider different airlines and compare prices",
                "Provide practical booking information and flight details",
                "Format results clearly with flight details, pricing, and timing information",
                "If no flights are found, suggest alternative nearby airports or dates"
            ],
            model=Gemini(id=settings.GEMINI_MODEL),
            tools=[SerpApiTools(api_key=self.serpapi_key)],
            add_datetime_to_instructions=True,
        )

    async def search_flights(self, source: str, destination: str, departure_date: date, return_date: date) -> Dict[str, Any]:
        """
        Search for flights using Gemini agent with SerpAPI tools
        """
        try:
            # Build search prompt
            prompt = self._build_flight_search_prompt(source, destination, departure_date, return_date)
            
            logger.info(f"Searching flights from {source} to {destination} using Gemini agent")
            
            # Run the agent
            result = self.agent.run(prompt, stream=False)
            
            if not result or not result.content:
                logger.warning("No content returned from flight search agent")
                return {
                    "flights": [],
                    "raw_response": {"error": "No content returned"},
                    "metadata": {
                        "search_successful": False,
                        "error": "No content returned"
                    }
                }
            
            # Process and structure the response
            processed_flights = self._process_flight_response(result.content)
            
            return {
                "flights": processed_flights,
                "raw_response": {
                    "agent_response": result.content,
                    "search_timestamp": datetime.now(UTC).isoformat()
                },
                "metadata": {
                    "search_successful": True,
                    "source": source.upper(),
                    "destination": destination.upper(),
                    "departure_date": departure_date.isoformat(),
                    "return_date": return_date.isoformat(),
                    "processed_count": len(processed_flights),
                    "search_timestamp": datetime.now(UTC).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Flight search error: {str(e)}")
            return {
                "flights": [],
                "raw_response": {"error": str(e)},
                "metadata": {
                    "search_successful": False,
                    "error": str(e)
                }
            }

    def _build_flight_search_prompt(self, source: str, destination: str, departure_date: date, return_date: date) -> str:
        """
        Build the search prompt for flight search
        """
        # Convert airport codes to full names for better search
        source_upper = source.upper()
        destination_upper = destination.upper()
        
        prompt = f"""
        Find the best round-trip flight options from {source_upper} to {destination_upper}.
        
        Flight Details:
        - Departure Airport: {source_upper}
        - Arrival Airport: {destination_upper}
        - Outbound Date: {departure_date.strftime('%Y-%m-%d (%A)')}
        - Return Date: {return_date.strftime('%Y-%m-%d (%A)')}
        - Currency: INR (Indian Rupees)
        
        Requirements:
        - Find the top 3-5 most affordable round-trip flight options
        - Include both direct flights and flights with connections
        - Search multiple airlines (IndiGo, Air India, SpiceJet, Vistara, GoFirst, etc.)
        - Compare prices across different booking platforms
        
        For each flight option, provide:
        - Airline name and flight numbers
        - Total price for round-trip in INR
        - Outbound flight: departure time, arrival time, duration
        - Return flight: departure time, arrival time, duration
        - Number of stops (direct or connecting)
        - Total travel time for round-trip
        - Booking website or platform information
        
        Format the response with clear sections for each flight option.
        Sort by price from lowest to highest.
        Include any important notes about baggage, meal services, or booking conditions.
        
        If no flights are available for the exact dates, suggest nearby dates or alternative airports.
        """
        
        return prompt

    def _process_flight_response(self, content: str) -> List[Dict[str, Any]]:
        """
        Process the agent response to extract structured flight data
        """
        try:
            flights = []
            
            # Split content into flight options
            flight_sections = self._split_flight_sections(content)
            
            for i, section in enumerate(flight_sections):
                flight_data = self._parse_flight_section(section, i + 1)
                if flight_data:
                    flights.append(flight_data)
            
            # Sort by price if possible
            flights = self._sort_flights_by_price(flights)
            
            return flights[:5]  # Return top 5 flights
            
        except Exception as e:
            logger.error(f"Error processing flight response: {str(e)}")
            return []

    def _split_flight_sections(self, content: str) -> List[str]:
        """
        Split content into individual flight option sections
        """
        lines = content.split('\n')
        sections = []
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new flight option
            if self._is_flight_option_header(line):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # Add the last section
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections

    def _is_flight_option_header(self, line: str) -> bool:
        """Check if line indicates start of a new flight option"""
        line_lower = line.lower()
        return (
            any(marker in line for marker in ['**', '##', '###']) or
            any(line.strip().startswith(f'{i}.') for i in range(1, 10)) or
            'option' in line_lower or
            'flight' in line_lower and ('₹' in line or 'inr' in line_lower)
        )

    def _parse_flight_section(self, section: str, option_number: int) -> Optional[Dict[str, Any]]:
        """
        Parse individual flight section to extract structured data
        """
        try:
            flight_data = {
                "airline": "Unknown Airline",
                "airline_logo": "",
                "price": "Not Available",
                "total_duration": "N/A",
                "departure_time": "",
                "arrival_time": "",
                "departure_airport": "",
                "arrival_airport": "",
                "booking_token": "",
                "departure_token": "",
                "flight_details": {
                    "outbound": {},
                    "return": {},
                    "stops": "Unknown",
                    "booking_info": ""
                }
            }
            
            lines = section.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                line_lower = line.lower()
                
                # Extract airline
                if 'airline' in line_lower or any(airline in line_lower for airline in ['indigo', 'air india', 'spicejet', 'vistara', 'goair']):
                    flight_data["airline"] = self._extract_airline_name(line)
                
                # Extract price
                if '₹' in line or 'inr' in line_lower or 'price' in line_lower:
                    price = self._extract_price(line)
                    if price:
                        flight_data["price"] = price
                
                # Extract departure/arrival times
                if 'departure' in line_lower and ('time' in line_lower or ':' in line):
                    flight_data["departure_time"] = self._extract_time(line)
                
                if 'arrival' in line_lower and ('time' in line_lower or ':' in line):
                    flight_data["arrival_time"] = self._extract_time(line)
                
                # Extract duration
                if 'duration' in line_lower or 'travel time' in line_lower:
                    duration = self._extract_duration(line)
                    if duration:
                        flight_data["total_duration"] = duration
                
                # Extract stops information
                if 'stop' in line_lower or 'direct' in line_lower or 'non-stop' in line_lower:
                    flight_data["flight_details"]["stops"] = line
                
                # Extract booking information
                if 'booking' in line_lower or 'website' in line_lower:
                    flight_data["flight_details"]["booking_info"] = line
            
            # If no airline found, try to extract from the first line
            if flight_data["airline"] == "Unknown Airline":
                first_line = lines[0] if lines else ""
                flight_data["airline"] = self._extract_airline_name(first_line) or f"Flight Option {option_number}"
            
            return flight_data
            
        except Exception as e:
            logger.error(f"Error parsing flight section: {str(e)}")
            return None

    def _extract_airline_name(self, text: str) -> str:
        """Extract airline name from text"""
        text = text.replace('*', '').replace('#', '').strip()
        
        # Known airline patterns
        airlines = {
            'indigo': 'IndiGo',
            'air india': 'Air India',
            'spicejet': 'SpiceJet',
            'vistara': 'Vistara',
            'goair': 'Go First',
            'akasa': 'Akasa Air',
            'alliance air': 'Alliance Air'
        }
        
        text_lower = text.lower()
        for key, name in airlines.items():
            if key in text_lower:
                return name
        
        # Try to extract from formatted text
        words = text.split()
        if words:
            # Remove numbering if present
            if words[0].endswith('.') and words[0][:-1].isdigit():
                words = words[1:]
            
            # Take first 2-3 words as airline name
            if len(words) >= 2:
                return ' '.join(words[:2])
            elif words:
                return words[0]
        
        return "Unknown Airline"

    def _extract_price(self, text: str) -> Optional[str]:
        """Extract price from text"""
        
        # Look for INR amounts
        price_patterns = [
            r'₹\s*[\d,]+',
            r'INR\s*[\d,]+',
            r'Rs\.?\s*[\d,]+',
            r'[\d,]+\s*INR',
            r'[\d,]+\s*₹'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None

    def _extract_time(self, text: str) -> str:
        """Extract time from text"""
        # Look for time patterns
        time_pattern = r'\d{1,2}:\d{2}(?:\s*[AaPp][Mm])?'
        match = re.search(time_pattern, text)
        
        if match:
            return match.group().strip()
        
        return ""

    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract duration from text"""
        # Look for duration patterns
        duration_patterns = [
            r'\d+h\s*\d+m',
            r'\d+\s*hours?\s*\d+\s*minutes?',
            r'\d+:\d+',
            r'\d+h\s*\d+min'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None

    def _sort_flights_by_price(self, flights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort flights by price"""
        def extract_price_value(flight):
            price_str = flight.get("price", "")
            if not price_str or price_str == "Not Available":
                return float('inf')
            
            numbers = re.findall(r'[\d,]+', str(price_str))
            if numbers:
                try:
                    return float(numbers[0].replace(',', ''))
                except ValueError:
                    return float('inf')
            return float('inf')
        
        return sorted(flights, key=extract_price_value)

    async def get_booking_link(self, booking_token: str, departure_token: str) -> str:
        """
        Generate booking link - for Gemini-based results, return a generic search link
        """
        try:
            if booking_token and booking_token.startswith("http"):
                return booking_token
            
            # Return generic flight search link
            return "https://www.google.com/travel/flights"
            
        except Exception as e:
            logger.error(f"Error generating booking link: {str(e)}")
            return "#"

    def _extract_cheapest_flights(self, flight_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Legacy method for backward compatibility - now handled by _process_flight_response
        """
        return flight_data[:3]

    def _format_flight_data(self, flight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Legacy method for backward compatibility - now handled by _parse_flight_section
        """
        return flight

    def _extract_price_value(self, price_str: str) -> float:
        """
        Legacy method for backward compatibility
        """
        try:
            if not price_str or price_str == "Not Available":
                return float('inf')
            
            numbers = re.findall(r'[\d,]+', str(price_str))
            if numbers:
                return float(numbers[0].replace(',', ''))
            return float('inf')
            
        except (ValueError, IndexError):
            return float('inf')