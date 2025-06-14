# Standard Library Imports
import logging
from typing import Dict, Any
from datetime import datetime, UTC

# Third-Party Imports
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini

# Application-Specific Imports
from config import settings

logger = logging.getLogger(__name__)

class HotelsRestaurantsService:
    def __init__(self):
        self.google_api_key = settings.GOOGLE_API_KEY
        self.serpapi_key = settings.SERPAPI_API_KEY
        
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        if not self.serpapi_key:
            raise ValueError("SERPAPI_API_KEY environment variable is required")
        
        # Initialize the agent
        self.agent = Agent(
            name="Hotel & Restaurant Finder",
            instructions=[
                "Find excellent hotels suitable for the specified travel theme and preferences",
                "Find highly-rated restaurants matching the user's activity preferences and cuisine interests",
                "For each hotel, include: name, address, price range, rating, brief description, and amenities",
                "For each restaurant, include: name, address, price range, rating, cuisine type, and brief description",
                "Focus on establishments near popular attractions and tourist areas",
                "Consider the user's budget preference when recommending options",
                "Format results clearly with separate sections for Hotels and Restaurants",
                "Provide 3-5 recommendations for each category",
                "If specific preferences aren't found, suggest similar alternatives",
                "Include practical information like booking websites or contact details when available"
            ],
            model=Gemini(id=settings.GEMINI_MODEL),
            tools=[SerpApiTools(api_key=self.serpapi_key)],
            add_datetime_to_instructions=True,
        )

    async def search_hotels_restaurants(
        self,
        destination: str,
        theme: str = "General",
        activity_preferences: str = "Sightseeing and local experiences",
        hotel_rating: str = "Any",
        budget: str = "Any"
    ) -> Dict[str, Any]:
        """
        Search for hotels and restaurants using Gemini agent with SerpAPI tools
        """
        try:
            # Construct the search prompt
            prompt = self._build_search_prompt(
                destination, theme, activity_preferences, hotel_rating, budget
            )
            
            logger.info(f"Searching hotels and restaurants for {destination}")
            
            # Run the agent
            result = self.agent.run(prompt, stream=False)
            
            if not result or not result.content:
                logger.warning("No content returned from hotels/restaurants agent")
                return {
                    "content": "No hotel or restaurant recommendations found for the specified criteria.",
                    "hotels": [],
                    "restaurants": [],
                    "metadata": {
                        "search_successful": False,
                        "error": "No content returned"
                    }
                }
            
            # Process and structure the response
            processed_result = self._process_agent_response(result.content)
            
            return {
                "content": result.content,
                "hotels": processed_result.get("hotels", []),
                "restaurants": processed_result.get("restaurants", []),
                "metadata": {
                    "search_successful": True,
                    "destination": str(destination),
                    "theme": str(theme),
                    "hotel_rating": str(hotel_rating),
                    "budget": str(budget),
                    "search_timestamp": datetime.now(UTC).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Hotels/restaurants search error: {str(e)}")
            return {
                "content": f"Error occurred while searching for hotels and restaurants: {str(e)}",
                "hotels": [],
                "restaurants": [],
                "metadata": {
                    "search_successful": False,
                    "error": str(e)
                }
            }

    def _build_search_prompt(
        self,
        destination: str,
        theme: str,
        activity_preferences: str,
        hotel_rating: str,
        budget: str
    ) -> str:
        """
        Build the search prompt for the agent
        """
        # Map hotel rating to search terms
        rating_mapping = {
            "Any": "hotels",
            "3": "3-star hotels",
            "4": "4-star hotels", 
            "5": "5-star luxury hotels"
        }
        
        hotel_search_term = rating_mapping.get(hotel_rating, "hotels")
        
        # Build comprehensive prompt
        prompt = f"""
        Find the best hotels and restaurants in {destination} for a {theme.lower()} trip.
        
        Requirements:
        - Hotel Rating: {hotel_rating} ({hotel_search_term})
        - Budget Level: {budget}
        - Travel Theme: {theme}
        - Activity Preferences: {activity_preferences}
        
        For Hotels, find 3-5 options that include:
        - Hotel name and star rating
        - Location/address (especially near attractions)
        - Price range per night in local currency
        - Guest rating/review score
        - Key amenities (pool, spa, breakfast, etc.)
        - Brief description highlighting what makes it suitable for {theme.lower()}
        
        For Restaurants, find 3-5 options that include:
        - Restaurant name
        - Cuisine type
        - Location/address
        - Price range (budget-friendly, mid-range, upscale)
        - Rating/review score
        - Specialty dishes or unique features
        - Brief description of atmosphere and why it fits the travel preferences
        
        Focus on establishments that match the {budget.lower()} budget level and are well-suited for {theme.lower()}.
        Consider the activity preferences: {activity_preferences}
        
        Format the response with clear "HOTELS" and "RESTAURANTS" section headers.
        """
        
        return prompt

    def _process_agent_response(self, content: str) -> Dict[str, Any]:
        """
        Process the agent response to extract structured data
        """
        try:
            # Initialize result structure
            result = {
                "hotels": [],
                "restaurants": []
            }
            
            # Split content into sections
            sections = self._split_content_sections(content)
            
            # Process each section
            for section_name, section_content in sections.items():
                if "hotel" in section_name.lower():
                    result["hotels"] = self._parse_recommendations(section_content, "hotel")
                elif "restaurant" in section_name.lower() or "dining" in section_name.lower():
                    result["restaurants"] = self._parse_recommendations(section_content, "restaurant")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing agent response: {str(e)}")
            return {"hotels": [], "restaurants": []}

    def _split_content_sections(self, content: str) -> Dict[str, str]:
        """
        Split content into sections based on headers
        """
        sections = {}
        lines = content.split('\n')
        current_section = "general"
        current_content = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check for section headers
            if any(keyword in line_lower for keyword in ["hotel", "restaurant", "dining", "accommodation"]):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line_lower
                current_content = [line]
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections

    def _parse_recommendations(self, section_text: str, rec_type: str) -> list:
        """
        Parse individual recommendations from a section with enhanced extraction
        """
        try:
            recommendations = []
            lines = section_text.split('\n')
            current_rec = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Enhanced pattern matching for recommendation headers
                if self._is_recommendation_header(line):
                    # Save previous recommendation
                    if current_rec and 'name' in current_rec:
                        recommendations.append(current_rec)
                    
                    # Start new recommendation
                    current_rec = {
                        'name': self._extract_name(line),
                        'type': rec_type,
                        'description': '',
                        'details': []
                    }
                elif current_rec:
                    # Add details to current recommendation
                    if self._contains_structured_info(line):
                        current_rec['details'].append(line)
                    else:
                        if current_rec['description']:
                            current_rec['description'] += ' ' + line
                        else:
                            current_rec['description'] = line
            
            # Add the last recommendation
            if current_rec and 'name' in current_rec:
                recommendations.append(current_rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error parsing {rec_type} recommendations: {str(e)}")
            return []

    def _is_recommendation_header(self, line: str) -> bool:
        """Check if line is a recommendation header"""
        line_lower = line.lower()
        return (
            any(marker in line for marker in ['**', '##', '###']) or
            any(line.strip().startswith(f'{i}.') for i in range(1, 10)) or
            (len(line.split()) <= 5 and not line.startswith('-') and not line.startswith('•'))
        )

    def _extract_name(self, line: str) -> str:
        """Extract clean name from header line"""
        # Remove formatting
        name = line.replace('*', '').replace('#', '').strip()
        
        # Remove numbering
        if name and name[0].isdigit() and '.' in name[:3]:
            name = name.split('.', 1)[1].strip()
        
        return name

    def _contains_structured_info(self, line: str) -> bool:
        """Check if line contains structured information like price, rating, etc."""
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in [
            'price', 'rating', 'star', '$', '€', '£', '₹', 'address', 'location', 
            'cuisine', 'amenities', 'phone', 'website', 'hours'
        ])

    async def get_hotel_details(self, hotel_name: str, destination: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific hotel
        """
        try:
            prompt = f"Provide detailed information about {hotel_name} in {destination}, including exact address, amenities, pricing, and booking information."
            
            result = self.agent.run(prompt, stream=False)
            
            return {
                "hotel_name": hotel_name,
                "destination": destination,
                "details": result.content if result else "No details found",
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting hotel details: {str(e)}")
            return {
                "hotel_name": hotel_name,
                "destination": destination,
                "details": f"Error retrieving details: {str(e)}",
                "timestamp": datetime.now(UTC).isoformat()
            }

    async def get_restaurant_details(self, restaurant_name: str, destination: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific restaurant
        """
        try:
            prompt = f"Provide detailed information about {restaurant_name} in {destination}, including cuisine type, menu highlights, pricing, hours, and reservation information."
            
            result = self.agent.run(prompt, stream=False)
            
            return {
                "restaurant_name": restaurant_name,
                "destination": destination,
                "details": result.content if result else "No details found",
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting restaurant details: {str(e)}")
            return {
                "restaurant_name": restaurant_name,
                "destination": destination,
                "details": f"Error retrieving details: {str(e)}",
                "timestamp": datetime.now(UTC).isoformat()
            }