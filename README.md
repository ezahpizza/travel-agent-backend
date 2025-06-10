# AI Travel Planner Backend

This is a production-ready FastAPI backend for an AI-powered travel planning application. It integrates with Google Gemini, SerpAPI, and MongoDB to provide intelligent travel research, flight search, hotel and restaurant recommendations, and itinerary generation.

## Features
- Flight search and history
- Destination research using LLMs and web search
- Hotel and restaurant recommendations
- AI-generated travel itineraries
- MongoDB-based caching and history
- Modular, extensible, and fully async

## Technology Stack
- Python 3.10+
- FastAPI
- MongoDB
- Serper(for web search)
- Google Gemini (for LLM-powered research and planning)
- Pydantic (for data validation)

## Setup
1. Clone the repository.
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Set environment variables for your API keys and MongoDB connection string (see `.env.example`).
4. Run the server:
   ```powershell
   uvicorn main:app --reload
   ```

## API Endpoints

### Flights (`/flights`)

- **POST `/flights/search`**
  - Search for flights using SerpAPI and return the top 3 cheapest options.
  - **Request Body:**
    - `source` (str): Departure airport IATA code
    - `destination` (str): Arrival airport IATA code
    - `departure_date` (date): Departure date
    - `return_date` (date): Return date
  - **Response:** List of flight options with airline, price, duration, etc.

- **GET `/flights/search/history`**
  - Get recent flight search history.
  - **Response:** List of recent flight search queries and results.

### Research (`/research`)

- **POST `/research/destination`**
  - Research a destination using Gemini agent and SerpAPI tools.
  - **Request Body:**
    - `destination` (str): City or country
    - `theme` (str): Travel theme (e.g., adventure, culture)
    - `activities` (str): Preferred activities
    - `num_days` (int): Trip duration
    - `budget` (enum): Economy, Standard, Luxury
    - `flight_class` (enum): Economy, Business, First Class
    - `hotel_rating` (enum): Any, 3⭐, 4⭐, 5⭐
    - `visa_required` (bool)
    - `insurance_required` (bool)
  - **Response:** Research summary, attractions, recommendations, safety tips.

- **GET `/research/destination/{destination}/history`**
  - Get research history for a specific destination.
  - **Response:** List of previous research queries and results for the destination.

### Hotels & Restaurants (`/hotels-restaurants`)

- **POST `/hotels-restaurants/search`**
  - Search for hotels and restaurants using Gemini agent and SerpAPI.
  - **Request Body:**
    - `destination` (str): City or country
    - `theme` (str): Travel theme
    - `activity_preferences` (str): Activity preferences
    - `hotel_rating` (enum): Any, 3⭐, 4⭐, 5⭐
  - **Response:** List of recommended hotels and restaurants with details.

- **GET `/hotels-restaurants/destination/{destination}/history`**
  - Get search history for hotels and restaurants by destination.
  - **Response:** List of previous hotel/restaurant searches for the destination.

### Itinerary (`/itinerary`)

- **POST `/itinerary/generate`**
  - Generate a complete travel itinerary using Gemini agent.
  - **Request Body:**
    - `destination` (str)
    - `theme` (str)
    - `activities` (str)
    - `num_days` (int)
    - `budget` (enum)
    - `flight_class` (enum)
    - `hotel_rating` (enum)
    - `visa_required` (bool)
    - `insurance_required` (bool)
    - `research_summary` (str)
    - `selected_flights` (list)
    - `hotel_restaurant_summary` (str)
  - **Response:** Detailed itinerary with daily plans, activities, tips, and cost estimates.

- **GET `/itinerary/destination/{destination}`**
  - Get itineraries for a specific destination with pagination.
  - **Query Parameters:**
    - `limit` (int): Number of results to return (default: 10)
    - `offset` (int): Number of results to skip (default: 0)
  - **Response:** List of itineraries for the destination.

- **GET `/itinerary/{itinerary_id}`**
  - Get a specific itinerary by its ID.
  - **Response:** The full itinerary details.

## Error Handling
- All endpoints return a consistent JSON structure:
  ```json
  {
    "success": true,
    "message": "...",
    "data": {...}
  }
  ```
- On error, `success` is `false` and `message` describes the error.

## Testing
- Tests are located in the `tests/` directory.
- To run tests:
  ```powershell
  pytest
  ```
- Tests are fully isolated from the production database.

## Contributing
- Fork the repo and create a feature branch.
- Submit a pull request with a clear description of your changes.

## License
This project is licensed under the MIT License.
