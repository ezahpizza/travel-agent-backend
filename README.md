# Navite Backend

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
    - `source` (str): Departure airport IATA code (3-letter code)
    - `destination` (str): Arrival airport IATA code (3-letter code)
    - `departure_date` (date): Departure date (YYYY-MM-DD)
    - `return_date` (date): Return date (YYYY-MM-DD)
    - `userid` (str): User ID from Clerk authentication
  - **Response:**
    - List of flight options with airline, price, duration, etc.

- **GET `/flights/search/history`**
  - Get recent flight search history for a user.
  - **Query Parameters:**
    - `userid` (str): User ID from Clerk authentication
    - `limit` (int): Number of records to return (default: 10)
  - **Response:**
    - List of recent flight search queries and results.

---

### Research (`/research`)

- **POST `/research/destination`**
  - Research a destination using Gemini agent and SerpAPI tools.
  - **Request Body:**
    - `destination` (str): City or country
    - `theme` (str): Travel theme (e.g., adventure, culture)
    - `activities` (str): Preferred activities
    - `num_days` (int): Trip duration in days
    - `budget` (enum): Economy, Standard, Luxury
    - `flight_class` (enum): Economy, Business, First Class
    - `hotel_rating` (enum): Any, 3, 4, 5
    - `visa_required` (bool)
    - `insurance_required` (bool)
    - `userid` (str): User ID from Clerk authentication
  - **Response:**
    - Research summary, attractions, recommendations, safety tips.

- **GET `/research/destination/{destination}/history`**
  - Get research history for a specific destination and user.
  - **Query Parameters:**
    - `userid` (str): User ID from Clerk authentication
    - `limit` (int): Number of records to return (default: 5)
  - **Response:**
    - List of previous research queries and results for the destination.

---

### Hotels & Restaurants (`/hotels-restaurants`)

- **POST `/hotels-restaurants/search`**
  - Search for hotels and restaurants using Gemini agent and SerpAPI.
  - **Request Body:**
    - `destination` (str): City or country
    - `theme` (str): Travel theme
    - `activity_preferences` (str): Activity preferences
    - `hotel_rating` (enum): Any, 3, 4, 5
    - `budget` (str): Budget level
    - `userid` (str): User ID from Clerk authentication
  - **Response:**
    - List of recommended hotels and restaurants with details.

- **GET `/hotels-restaurants/destination/{destination}/history`**
  - Get search history for hotels and restaurants by destination and user.
  - **Query Parameters:**
    - `userid` (str): User ID from Clerk authentication
    - `limit` (int): Number of records to return (default: 5)
  - **Response:**
    - List of previous hotel/restaurant searches for the destination.

---

### Itinerary (`/itinerary`)

- **POST `/itinerary/generate`**
  - Generate a complete travel itinerary using Gemini agent.
  - **Request Body:**
    - `destination` (str): City or country
    - `theme` (str): Travel theme
    - `activities` (str): Preferred activities
    - `num_days` (int): Trip duration in days
    - `budget` (enum): Economy, Standard, Luxury
    - `flight_class` (enum): Economy, Business, First Class
    - `hotel_rating` (enum): Any, 3, 4, 5
    - `visa_required` (bool)
    - `insurance_required` (bool)
    - `userid` (str): User ID from Clerk authentication
  - **Response:**
    - Detailed itinerary with daily plans, activities, tips, and cost estimates.

- **GET `/itinerary/destination/{destination}`**
  - Get itineraries for a specific destination with pagination.
  - **Query Parameters:**
    - `limit` (int): Number of results to return (default: 10)
    - `offset` (int): Number of results to skip (default: 0)
  - **Response:**
    - List of itineraries for the destination.

- **GET `/itinerary/{itinerary_id}`**
  - Get a specific itinerary by its ID.
  - **Response:**
    - The full itinerary details.

- **GET `/itinerary/history`**
  - Get recent itinerary history for a specific user.
  - **Query Parameters:**
    - `userid` (str): User ID from Clerk authentication
    - `limit` (int): Number of records to return (default: 10)
  - **Response:**
    - List of recent itineraries for the user.

---

### Subscription & Paywall (`/subscription`)

- **GET `/subscription/status`**
  - Get the current subscription plan and POST usage for a user.
  - **Query Parameters:**
    - `userid` (str): User ID from Clerk authentication
  - **Response:**
    - `plan` (str): "basic" or "paid"
    - `usage_this_month` (int): Number of POST calls this month

- **POST `/subscription/create-session`**
  - Create a Stripe Checkout session for the paid plan (dev/test mode supported).
  - **Request Body:**
    - `userid` (str): User ID from Clerk authentication
    - `success_url` (str): URL to redirect after successful payment (should include `session_id` as a query param)
    - `cancel_url` (str): URL to redirect if payment is cancelled
  - **Response:**
    - `session` (object): Stripe Checkout session object (use `session.url` to redirect user)

- **POST `/subscription/verify-payment`**
  - Verify a Stripe payment and activate the paid plan for the user.
  - **Request Body:**
    - `userid` (str): User ID from Clerk authentication
    - `session_id` (str): Stripe Checkout session ID
  - **Response:**
    - `{ "success": true }` on success

#### Paywall Enforcement
- All POST endpoints for core services (e.g., `/flights/search`, `/itinerary/generate`, etc.) are rate-limited for free users (15 POSTs/month). Paid users have unlimited access. GET endpoints are always unlimited.
- If a free user exceeds their POST limit, a 429 error is returned:
  ```json
  {
    "success": false,
    "message": "Free plan limit reached (15 POST calls/month). Please upgrade.",
    "data": null
  }
  ```

#### Subscription Plans
- **Basic Explorer (Free):** 15 POST API calls/month, unlimited GET calls.
- **Travel Master (Paid):** Unlimited POST/GET calls. $1.99/month (USD, Stripe test mode supported).

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
