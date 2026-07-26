# HeyPico Local Maps Assistant API

FastAPI backend for bilingual local place discovery. Phase 1 provides health
monitoring and normalized Google Places Text Search. Phase 2 & 2.1 add a structured
chat endpoint that uses a local Ollama model for intent classification, request-scoped
conversational history, place-search refinement, price-aware place search, and concise
general replies.

The local model never supplies factual place results. Place names, ratings,
addresses, coordinates, price levels, opening status, and Maps links come only from the
normalized Google Places API response.

## Requirements

- Python 3.11 or newer
- A Google Cloud project with Places API (New) enabled
- A restricted server-side Google Places API key
- [Ollama for Windows](https://ollama.com/download/windows)
- The local `qwen3:4b` model

Install and verify the model:

```powershell
ollama pull qwen3:4b
ollama run qwen3:4b
```

Press `Ctrl+C` to leave the interactive model session. Verify the local API:

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:11434/api/tags"
```

## Structure

```text
app/
  core/       Configuration, errors, and rate limiting
  routers/    Health, places, and chat endpoints
  schemas/    Typed requests, history, context, intent analysis, and API responses
  services/   Google Places, Ollama, and chat orchestration
  main.py     FastAPI application factory and shared HTTP client
tests/        Mocked API and service-boundary tests
```

## Setup

From `apps/api` in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Do not overwrite an existing `.env`. Configure it with:

```dotenv
GOOGLE_PLACES_API_KEY=
ALLOWED_ORIGINS=http://localhost:3000
APP_ENV=development
GOOGLE_PLACES_TIMEOUT_SECONDS=15
PLACES_RATE_LIMIT=30/minute
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:4b
OLLAMA_CONVERSATION_MODEL=
OLLAMA_TIMEOUT_SECONDS=90
CHAT_RATE_LIMIT=20/minute
GOOGLE_PLACES_LOCATION_BIAS_RADIUS_METERS=5000
```

`OLLAMA_CONVERSATION_MODEL` is optional. When set, it handles natural responses
while `OLLAMA_MODEL` remains the structured planner model.

Multiple CORS origins can be comma-separated. Start the backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

Swagger UI is available at `http://localhost:8000/docs`.

## Endpoints

- `GET /health`
- `GET /api/places/search?query=restoran+sunda+di+Bogor`
- `POST /api/chat`

## Conversational Context & Refinements (Phase 2.1)

The `POST /api/chat` endpoint is request-scoped and stateless. The backend does not maintain server-side conversation databases or Redis stores. Instead, clients pass recent text messages in `history` and the structured context from the previous search in `context`.

Supported intents:
- `place_search`: Starts a new independent search.
- `place_refinement`: Modifies prior search context (e.g. price, rating, category, location, or alternatives).
- `general`: General conversation or greeting.
- `unsupported`: Requests outside assistant capabilities.

Supported refinements:
- `cheaper`: Filters by Google Places `priceLevels` (`PRICE_LEVEL_INEXPENSIVE`). Fallback expands to `PRICE_LEVEL_MODERATE` if empty; `PRICE_LEVEL_FREE` is accepted only when returned by Google, never sent as a request filter.
- `higher_rated`: Sorts verified places by rating descending, then review count descending.
- `open_now`: Filters open places.
- `closer`: Requires coordinates or explicit location.
- `different_location`: Preserves search category, replaces location.
- `different_category`: Replaces search category, preserves location.
- `alternatives`: Excludes previously returned place IDs.

### Example Refinement Request Sequence

**Request 1 (Initial Search):**

```json
{
  "message": "Cari bakso di sekitar Gadog, Kabupaten Bogor"
}
```

**Response 1:**

```json
{
  "message": "Saya menemukan 5 bakso di sekitar Gadog, Kabupaten Bogor.",
  "intent": "place_search",
  "requires_location": false,
  "search_query": "bakso di sekitar Gadog, Kabupaten Bogor",
  "places": [...],
  "context": {
    "last_intent": "place_search",
    "last_search_terms": "bakso",
    "last_location": "Gadog, Kabupaten Bogor",
    "last_search_query": "bakso di sekitar Gadog, Kabupaten Bogor",
    "last_place_ids": ["place-1", "place-2"]
  }
}
```

**Request 2 (Follow-up Refinement):**

```json
{
  "message": "yang budget menu nya agak murah dimana?",
  "history": [
    {"role": "user", "content": "Cari bakso di sekitar Gadog, Kabupaten Bogor"},
    {"role": "assistant", "content": "Saya menemukan 5 bakso di sekitar Gadog, Kabupaten Bogor."}
  ],
  "context": {
    "last_intent": "place_search",
    "last_search_terms": "bakso",
    "last_location": "Gadog, Kabupaten Bogor",
    "last_search_query": "bakso di sekitar Gadog, Kabupaten Bogor",
    "last_place_ids": ["place-1", "place-2"]
  }
}
```

**Response 2:**

```json
{
  "message": "Berdasarkan tingkat harga yang tersedia di Google Maps, saya menemukan 3 opsi bakso yang cenderung lebih terjangkau di sekitar Gadog, Kabupaten Bogor.",
  "intent": "place_refinement",
  "requires_location": false,
  "search_query": "bakso murah di Gadog, Kabupaten Bogor",
  "places": [...],
  "context": {
    "last_intent": "place_refinement",
    "last_search_terms": "bakso",
    "last_location": "Gadog, Kabupaten Bogor",
    "last_search_query": "bakso murah di Gadog, Kabupaten Bogor",
    "last_place_ids": ["place-3", "place-4"]
  }
}
```

## Price Level Limitations

- Google Places `priceLevel` provides categorical indicator levels (`PRICE_LEVEL_INEXPENSIVE`, `PRICE_LEVEL_MODERATE`, etc.), not exact itemized menu prices.
- Some places on Google Maps do not supply `priceLevel` data.
- The assistant qualifies price responses as *"tenderung lebih terjangkau berdasarkan tingkat harga Google Maps"* and never claims exact item menu pricing.

## Tests

Automated tests mock both Google Places and Ollama. They never call the internet or `localhost:11434`:

```powershell
pytest
```

## Security

Never commit `.env` or expose the Google server key to browser code, API
responses, logs, or client-side environment variables. Restrict the key in
Google Cloud to Places API (New), apply the narrowest practical server/API
restrictions, monitor quota, and rotate it if exposed. CORS does not make a
browser-exposed key safe. Raw Ollama and Google responses are never returned.

## Known Limitations

- Server-side conversation persistence (database/Redis) is intentionally not implemented. The client is responsible for sending `history` and `context`.
- Price level filter depends on Google Maps metadata availability.
- Proximity ordering requires user coordinates for high accuracy.

## Manual Smoke Test

1. Verify Ollama: `ollama --version`.
2. Verify the model: `ollama list`.
3. Verify the API: `Invoke-RestMethod -Method Get -Uri "http://localhost:11434/api/tags"`.
4. Start the backend: `uvicorn app.main:app --reload --port 8000`.
5. Open `http://localhost:8000/docs`.
6. Test `{"message":"Cari bakso di Gadog, Kabupaten Bogor"}`.
7. Send follow-up `{"message":"yang lebih murah?", "context": {...}}` and verify category and location inheritance.
8. Confirm general messages preserve previous search context without clearing it.


## Final stabilization notes

The chat orchestration now also supports:

- result-count requests up to 20 results
- deterministic open-now post-filtering
- verified 24-hour detection from Google opening-hour periods
- nearest-result ranking using verified coordinates and Haversine distance
- lightweight prior-place references for follow-up detail questions
- Place Details lookups for address, rating, directions, and closing-time requests
- natural acknowledgement replies such as `makasih` and `thanks`
- controlled Google fallback when optional price filters are rejected

Exact menu prices remain outside the available Google Places data and are never fabricated.
