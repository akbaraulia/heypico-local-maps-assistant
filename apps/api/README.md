# HeyPico Local Maps Assistant API

FastAPI backend for local place discovery through Google Places API (New).
Phase 1 provides health monitoring and normalized text search results. It does
not include a frontend, database, authentication, chat, LLMs, or AI agents.

## Requirements

- Python 3.11 or newer
- A Google Cloud project with Places API (New) enabled
- A server-side Google Places API key

## Structure

```text
app/
  core/       Configuration, errors, and rate limiting
  routers/    Health and places HTTP endpoints
  schemas/    Request and response models
  services/   Google Places integration and normalization
  main.py     FastAPI application factory
tests/        Mocked API and service-boundary tests
```

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `GOOGLE_PLACES_API_KEY`. The other settings have safe
development defaults:

```dotenv
GOOGLE_PLACES_API_KEY=
ALLOWED_ORIGINS=http://localhost:3000
APP_ENV=development
GOOGLE_PLACES_TIMEOUT_SECONDS=15
PLACES_RATE_LIMIT=30/minute
```

Multiple CORS origins can be provided as a comma-separated value. Start the
API with:

```powershell
uvicorn app.main:app --reload --port 8000
```

Swagger UI is available at `http://localhost:8000/docs`.

## API

Health check:

```http
GET http://localhost:8000/health
```

Place search:

```http
GET http://localhost:8000/api/places/search?query=restoran+sunda+di+Bogor
```

Example response:

```json
{
  "query": "restoran sunda di Bogor",
  "count": 1,
  "places": [
    {
      "place_id": "example-place-id",
      "name": "Example Restaurant",
      "address": "Bogor, West Java",
      "rating": 4.5,
      "user_rating_count": 320,
      "open_now": true,
      "primary_type": "restaurant",
      "lat": -6.6,
      "lng": 106.8,
      "google_maps_url": "https://maps.google.com/example",
      "directions_url": "https://www.google.com/maps/dir/?api=1&destination_place_id=example-place-id"
    }
  ]
}
```

## Tests

All Google calls are replaced by an in-memory HTTP transport:

```powershell
pytest
```

## Security

Never commit `.env` or expose the server API key to browser code, API
responses, logs, or client-side environment variables. Restrict the key in
Google Cloud to Places API (New), apply the narrowest practical server/API
restrictions, monitor quota, and rotate it if exposed. CORS is not a secret
boundary and does not make a browser-exposed key safe.

LLM and chat integration are intentionally deferred to Phase 2.
