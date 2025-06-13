import os
import re
import logging
from typing import Dict, Any, List
from agno.agent import Agent
from agno.models.google import Gemini
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

class ItineraryService:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Initialize the planning agent
        self.planner = Agent(
            name="Travel Itinerary Planner",
            instructions=[
                "Create detailed day-by-day travel itineraries based on user preferences and research data",
                "Include specific timing, activities, meals, and transportation for each day",
                "Optimize schedules for convenience, travel time, and user enjoyment",
                "Balance must-see attractions with user's specific interests and activities",
                "Consider budget constraints and provide cost estimates where possible",
                "Include practical information like opening hours, booking requirements, and travel tips",
                "Structure itinerary with clear day divisions and time slots",
                "Provide alternative options for weather-dependent activities",
                "Include rest periods and meal breaks in the schedule",
                "Consider the travel theme and group type (family, couple, solo, etc.)",
                "Integrate recommended hotels and restaurants from previous research",
                "Provide estimated costs and booking information where relevant"
            ],
            model=Gemini(id="gemini-2.5-flash-preview-04-17"),
            add_datetime_to_instructions=True,
        )

    async def generate_itinerary(
        self,
        destination: str,
        theme: str,
        activities: str,
        num_days: int,
        budget: str,
        flight_class: str,
        hotel_rating: str,
        visa_required: bool,
        insurance_required: bool,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive travel itinerary using all provided information
        """
        try:
            # Build comprehensive prompt with all data
            prompt = self._build_itinerary_prompt(
                destination, theme, activities, num_days, budget, flight_class,
                hotel_rating, visa_required, insurance_required
            )
            
            logger.info(f"Generating {num_days}-day itinerary for {destination}")
            
            # Generate itinerary using the agent
            result = self.planner.run(prompt, stream=False)
            
            if not result or not result.content:
                logger.warning("No itinerary content returned from agent")
                return {
                    "itinerary": "Unable to generate itinerary with the provided information.",
                    "daily_breakdown": [],
                    "summary": {
                        "destination": destination,
                        "duration": num_days,
                        "theme": theme,
                        "status": "failed"
                    },
                    "metadata": {
                        "generation_successful": False,
                        "error": "No content returned"
                    }
                }
            
            # Process and structure the itinerary
            processed_itinerary = self._process_itinerary_response(
                result.content, num_days, destination, theme
            )
            
            return {
                "destination": destination,
                "total_days": num_days,
                "theme": theme,
                "daily_plans": processed_itinerary.get("daily_breakdown", []),
                "total_estimated_cost": f"${budget} Budget Level",
                "travel_tips": processed_itinerary.get("practical_tips", []),
                "packing_suggestions": self._extract_packing_suggestions(result.content),
                "itinerary": result.content,
                "summary": {
                    "destination": destination,
                    "duration": num_days,
                    "theme": theme,
                    "budget": budget,
                    "flight_class": flight_class,
                    "hotel_rating": hotel_rating,
                    "total_activities": len(processed_itinerary.get("activities", [])),
                    "status": "completed"
                },
                "practical_info": {
                    "visa_required": visa_required,
                    "insurance_required": insurance_required,
                    "budget_level": budget
                },
                "metadata": {
                    "generation_successful": True,
                    "generation_timestamp": datetime.now(UTC).isoformat(),
                }
            }
            
        except Exception as e:
            logger.error(f"Itinerary generation error: {str(e)}")
            return {
                "itinerary": f"Error occurred while generating itinerary: {str(e)}",
                "daily_breakdown": [],
                "summary": {
                    "destination": destination,
                    "duration": num_days,
                    "theme": theme,
                    "status": "error"
                },
                "metadata": {
                    "generation_successful": False,
                    "error": str(e)
                }
            }

    def _build_itinerary_prompt(
        self,
        destination: str,
        theme: str,
        activities: str,
        num_days: int,
        budget: str,
        flight_class: str,
        hotel_rating: str,
        visa_required: bool,
        insurance_required: bool
    ) -> str:
        """
        Build comprehensive prompt for itinerary generation
        """
        # Build the comprehensive prompt
        prompt = f"""
        Create a detailed {num_days}-day itinerary for a {theme.lower()} trip to {destination}.
        
        TRAVELER PREFERENCES:
        - Travel Theme: {theme}
        - Preferred Activities: {activities}
        - Budget Level: {budget}
        - Flight Class: {flight_class}
        - Hotel Rating Preference: {hotel_rating}
        - Visa Required: {"Yes" if visa_required else "No"}
        - Travel Insurance: {"Required" if insurance_required else "Optional"}
        
        ITINERARY REQUIREMENTS:
        1. Create a day-by-day schedule for all {num_days} days
        2. Include specific timings for activities (e.g., 9:00 AM - 12:00 PM)
        3. Balance popular attractions with user's specific interests: {activities}
        4. Include meal recommendations (breakfast, lunch, dinner)
        5. Add transportation details between locations
        6. Consider {budget.lower()} budget constraints
        7. Include rest periods and flexibility in the schedule
        8. Provide practical tips for each day
        9. Suggest backup indoor activities for weather concerns
        10. Include estimated costs where possible
        
        FORMAT:
        - Start with a brief overview
        - Organize by "Day 1", "Day 2", etc.
        - Use clear time slots for each activity
        - Include practical information and tips
        - End with packing suggestions and final tips
        
        Make this itinerary specifically tailored for {theme.lower()} travelers interested in {activities}.
        """
        
        return prompt

    def _process_itinerary_response(
        self, 
        content: str, 
        num_days: int, 
        destination: str, 
        theme: str
    ) -> Dict[str, Any]:
        """
        Process the itinerary response to extract structured data
        """
        try:
            result = {
                "daily_breakdown": [],
                "activities": [],
                "restaurants": [],
                "practical_tips": []
            }
            
            # Split content into days
            daily_sections = self._extract_daily_sections(content, num_days)
            
            for day_num in range(1, num_days + 1):
                day_content = daily_sections.get(day_num, "")
                activities = self._extract_activities_from_day(day_content)
                
                day_data = {
                    "day": day_num,
                    "theme": f"Day {day_num} - {theme}",
                    "activities": activities,
                    "estimated_cost": "Varies"
                }
                result["daily_breakdown"].append(day_data)
            
            # Extract overall data
            result["activities"] = self._extract_all_activities(content)
            result["restaurants"] = self._extract_all_restaurants(content)
            result["practical_tips"] = self._extract_practical_tips(content)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing itinerary response: {str(e)}")
            return {"daily_breakdown": [], "activities": [], "restaurants": [], "practical_tips": []}

    def _extract_daily_sections(self, content: str, num_days: int) -> Dict[int, str]:
        """
        Extract individual day sections from the itinerary
        """
        daily_sections = {}
        lines = content.split('\n')
        current_day = None
        current_content = []
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Look for day indicators
            day_match = None
            for day_num in range(1, num_days + 1):
                if f"day {day_num}" in line_lower or f"day{day_num}" in line_lower:
                    day_match = day_num
                    break
            
            if day_match:
                # Save previous day content
                if current_day and current_content:
                    daily_sections[current_day] = '\n'.join(current_content)
                
                # Start new day
                current_day = day_match
                current_content = [line]
            elif current_day:
                current_content.append(line)
        
        # Save last day
        if current_day and current_content:
            daily_sections[current_day] = '\n'.join(current_content)
        
        return daily_sections

    def _extract_activities_from_day(self, day_content: str) -> List[Dict[str, str]]:
        """Extract activities with time slots from a day's content"""
        activities = []
        lines = day_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for time patterns and activities
            if any(time_indicator in line.lower() for time_indicator in ['am', 'pm', ':']):
                activities.append({
                    "time": self._extract_time_from_line(line),
                    "activity": line,
                    "location": self._extract_location_from_line(line),
                    "duration": "",
                    "cost_estimate": "",
                    "notes": ""
                })
        
        return activities

    def _extract_location_from_line(self, line: str) -> str:
        """Extract location information from a line"""
        # Look for location indicators
        if ' at ' in line.lower():
            parts = line.lower().split(' at ')
            if len(parts) > 1:
                return parts[1].split(',')[0].strip().title()
        return ""

    def _extract_meals_from_day(self, day_content: str) -> List[Dict[str, str]]:
        """Extract meal recommendations from a day's content"""
        meals = []
        lines = day_content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(meal in line_lower for meal in ['breakfast', 'lunch', 'dinner', 'snack']):
                meals.append({
                    "time": self._extract_time_from_line(line),
                    "meal": line.strip(),
                    "type": self._identify_meal_type(line_lower)
                })
        
        return meals

    def _extract_time_from_line(self, line: str) -> str:
        """Extract time information from a line"""
        time_pattern = r'\b(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)|\d{1,2}\s*(?:AM|PM|am|pm))\b'
        match = re.search(time_pattern, line)
        return match.group(1) if match else ""

    def _identify_meal_type(self, line_lower: str) -> str:
        """Identify the type of meal from content"""
        if 'breakfast' in line_lower:
            return 'breakfast'
        elif 'lunch' in line_lower:
            return 'lunch'
        elif 'dinner' in line_lower:
            return 'dinner'
        elif 'snack' in line_lower:
            return 'snack'
        return 'meal'

    def _extract_transportation_from_day(self, day_content: str) -> List[str]:
        """Extract transportation mentions from day content"""
        transport_mentions = []
        lines = day_content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(transport in line_lower for transport in 
                   ['taxi', 'bus', 'metro', 'walk', 'uber', 'auto', 'rickshaw']):
                transport_mentions.append(line.strip())
        
        return transport_mentions

    def _extract_tips_from_day(self, day_content: str) -> List[str]:
        """Extract tips and practical advice from day content"""
        tips = []
        lines = day_content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(tip_indicator in line_lower for tip_indicator in 
                   ['tip:', 'note:', 'remember:', 'important:', 'advice:']):
                tips.append(line.strip())
        
        return tips

    def _extract_all_activities(self, content: str) -> List[str]:
        """Extract all activity mentions from the entire itinerary"""
        activities = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(activity in line_lower for activity in 
                   ['visit', 'explore', 'tour', 'museum', 'temple', 'fort', 'palace']):
                activities.append(line.strip())
        
        return list(set(activities))  # Remove duplicates

    def _extract_all_restaurants(self, content: str) -> List[str]:
        """Extract all restaurant mentions from the entire itinerary"""
        restaurants = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(food_word in line_lower for food_word in 
                   ['restaurant', 'cafe', 'dhaba', 'eatery', 'food']):
                restaurants.append(line.strip())
        
        return list(set(restaurants))  # Remove duplicates

    def _extract_practical_tips(self, content: str) -> List[str]:
        """Extract practical tips from the entire itinerary"""
        tips = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(tip_word in line_lower for tip_word in 
                   ['packing', 'tip', 'advice', 'remember', 'important', 'suggestion']):
                tips.append(line.strip())
        
        return tips
    
    def _extract_packing_suggestions(self, content: str) -> List[str]:
        """Extract packing suggestions from the entire itinerary"""
        suggestions = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(pack_word in line_lower for pack_word in 
                ['pack', 'bring', 'carry', 'essential', 'clothing', 'gear']):
                suggestions.append(line.strip())
        
        return suggestions[:10]  # Limit to 10 suggestions

    async def optimize_itinerary(
        self, 
        itinerary_content: str, 
        optimization_request: str
    ) -> Dict[str, Any]:
        """
        Optimize an existing itinerary based on user feedback
        """
        try:
            prompt = f"""
            Optimize the following itinerary based on this request: {optimization_request}
            
            Current Itinerary:
            {itinerary_content}
            
            Please provide an optimized version that addresses the user's request while maintaining
            the overall structure and quality of the original itinerary.
            """
            
            result = self.planner.run(prompt, stream=False)
            
            return {
                "optimized_itinerary": result.content if result else "Optimization failed",
                "optimization_request": optimization_request,
                "optimization_successful": bool(result and result.content),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Itinerary optimization error: {str(e)}")
            return {
                "optimized_itinerary": f"Optimization failed: {str(e)}",
                "optimization_request": optimization_request,
                "optimization_successful": False,
                "timestamp": datetime.now(UTC).isoformat()
            }