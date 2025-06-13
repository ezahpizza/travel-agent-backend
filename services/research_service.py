import os
import logging
from typing import Dict, Any, Optional
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini

from models.schemas import ResearchRequest

logger = logging.getLogger(__name__)

class ResearchService:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable is required")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        self._setup_agent()

    def _setup_agent(self):
        """Initialize the research agent"""
        self.researcher = Agent(
            name="Destination Researcher",
            instructions=[
                "You are a professional travel researcher specializing in destination analysis.",
                "Identify the travel destination specified by the user.",
                "Gather comprehensive information about the destination including:",
                "- Climate and best time to visit",
                "- Culture, customs, and local etiquette",
                "- Safety tips and travel advisories",
                "- Popular attractions and landmarks",
                "- Must-visit places and hidden gems",
                "- Activities matching user's interests and travel style",
                "- Local transportation options",
                "- Currency and typical costs",
                "- Visa requirements and entry procedures",
                "- Health recommendations and vaccinations",
                "Prioritize information from reliable sources and official travel guides.",
                "Structure your response with clear sections and actionable recommendations.",
                "Focus on practical, up-to-date information that helps with trip planning."
            ],
            model=Gemini(id="gemini-2.5-flash-preview-04-17"),
            tools=[SerpApiTools(api_key=self.api_key)],
            add_datetime_to_instructions=True,
        )

    async def research_destination(self, request: ResearchRequest) -> Optional[Dict[str, Any]]:
        """
        Research destination using Gemini agent with SerpAPI tools
        """
        try:
            research_prompt = self._build_research_prompt(request)
            
            logger.info(f"Starting research for {request.destination}")
            result = self.researcher.run(research_prompt, stream=False)
            
            if not result or not result.content:
                logger.warning("No research content returned from agent")
                return None
            
            # Parse and structure the research content
            research_data = self._parse_research_content(result.content, request)
            
            return research_data
            
        except Exception as e:
            logger.error(f"Research failed: {str(e)}")
            raise

    def _build_research_prompt(self, request: ResearchRequest) -> str:
        """
        Build comprehensive research prompt
        """
        prompt = f"""
        Research the destination: {request.destination}
        
        Trip Details:
        - Theme: {request.theme}
        - Duration: {request.num_days} days
        - Preferred Activities: {request.activities}
        - Budget Level: {request.budget}
        - Flight Class: {request.flight_class}
        - Hotel Rating: {request.hotel_rating}
        - Visa Required: {'Yes' if request.visa_required else 'No'}
        - Travel Insurance: {'Yes' if request.insurance_required else 'No'}
        
        Please provide:
        1. Destination Overview - location, climate, best time to visit
        2. Cultural Insights - customs, etiquette, local culture
        3. Safety Information - current safety situation, travel advisories
        4. Top Attractions - must-see places and landmarks
        5. Recommended Activities - matching the theme "{request.theme}" and interests "{request.activities}"
        6. Local Transportation - getting around the destination
        7. Budget Information - typical costs for {request.budget} budget
        8. Travel Requirements - visa, health, documentation needs
        9. Practical Tips - currency, language, communication
        10. Hidden Gems - lesser-known but worthwhile places
        
        Focus on current, accurate information that will help plan an amazing {request.theme.lower()} trip.
        """
        
        return prompt

    def _parse_research_content(self, content: str, request: ResearchRequest) -> Dict[str, Any]:
        """
        Parse and structure research content into organized format
        """
        try:
            # Extract key information sections
            attractions = self._extract_attractions(content)
            recommendations = self._extract_recommendations(content)
            safety_tips = self._extract_safety_tips(content)

            
            return {
                "destination": request.destination,
                "theme": request.theme,
                "attractions": attractions,
                "recommendations": recommendations,
                "safety_tips": safety_tips,
                "trip_duration": request.num_days,
                "budget_level": request.budget,
                "preferred_activities": request.activities
            }
            
        except Exception as e:
            logger.error(f"Error parsing research content: {str(e)}")
            return {
                "destination": request.destination,
                "theme": request.theme,
                "attractions": [],
                "recommendations": [],
                "safety_tips": []
            }

    def _extract_attractions(self, content: str) -> list:
        """Extract attractions from research content"""
        attractions = []
        try:
            lines = content.split('\n')
            in_attractions_section = False
            
            for line in lines:
                line = line.strip()
                if 'attraction' in line.lower() or 'landmark' in line.lower():
                    in_attractions_section = True
                    continue
                if in_attractions_section and line.startswith(('-', '*', '•')):
                    attraction = line.lstrip('-*•').strip()
                    if attraction and len(attraction) > 10:
                        attractions.append(attraction)
                elif in_attractions_section and line and not line.startswith(('-', '*', '•')):
                    if len(attractions) >= 10:  # Limit attractions
                        break
                    in_attractions_section = False
        except Exception as e:
            logger.error(f"Error extracting attractions: {str(e)}")
        
        return attractions[:10]  # Return top 10 attractions

    def _extract_recommendations(self, content: str) -> list:
        """Extract recommendations from research content"""
        recommendations = []
        try:
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'must']):
                    if line.startswith(('-', '*', '•')):
                        rec = line.lstrip('-*•').strip()
                        if rec and len(rec) > 15:
                            recommendations.append(rec)
                    elif len(line) > 20 and len(line) < 200:
                        recommendations.append(line)
        except Exception as e:
            logger.error(f"Error extracting recommendations: {str(e)}")
        
        return recommendations[:8]  # Return top 8 recommendations

    def _extract_safety_tips(self, content: str) -> list:
        """Extract safety tips from research content"""
        safety_tips = []
        try:
            lines = content.split('\n')
            in_safety_section = False
            
            for line in lines:
                line = line.strip()
                if 'safety' in line.lower() or 'security' in line.lower():
                    in_safety_section = True
                    continue
                if in_safety_section and line.startswith(('-', '*', '•')):
                    tip = line.lstrip('-*•').strip()
                    if tip and len(tip) > 10:
                        safety_tips.append(tip)
                elif in_safety_section and line and not line.startswith(('-', '*', '•')):
                    if len(safety_tips) >= 6:  # Limit safety tips
                        break
                    in_safety_section = False
        except Exception as e:
            logger.error(f"Error extracting safety tips: {str(e)}")
        
        return safety_tips[:6]  # Return top 6 safety tips