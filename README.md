# HeyPico.ai Code Test 2 — Implementation Report

## Candidate

**Akbar Aulia Ramadhan**

## Submission Overview

This repository contains my implementation for **HeyPico.ai Code Test 2**:

> Run a local LLM that can understand requests for places to go, eat, shop, stay, or explore, and display verified Google Maps results with embedded map and direction access.

I approached the assignment as a small end-to-end product rather than only a proof of concept. The result is a conversational local AI maps assistant with a local Qwen model, a Python API, verified Google Places data, geolocation support, contextual follow-up handling, an interactive map experience, and reproducible Docker-based setup.

---

## Requirement Coverage

| Test requirement | Implementation |
|---|---|
| Run a local LLM | Qwen runs locally through Ollama |
| Accept prompts asking for places | Conversational search supports Indonesian, English, and mixed-language requests |
| Show Google Maps results | Verified Google Places results are rendered as place cards and synchronized maps |
| Embedded map | The selected verified place is rendered using Google Maps Embed place mode |
| Open location or directions | Each result includes Google Maps and Directions actions |
| Backend in Python or JavaScript | FastAPI backend written in Python |
| Google Maps API best practices | Server-side key separation, environment variables, API restrictions guidance, request validation, timeouts, and controlled error handling |
| Explain assumptions | Assumptions and limitations are documented below |
| AI-assisted coding permitted | AI assistance was used as an engineering accelerator, with manual testing, debugging, architecture decisions, and integration validation |

---

## What I Built

### 1. Local conversational AI

The assistant uses a locally running **Qwen model through Ollama**.

The LLM is responsible for:

- understanding natural-language requests;
- recognizing place categories and locations;
- interpreting Indonesian, English, slang, and mixed-language prompts;
- understanding contextual refinements;
- resolving references to previous results;
- generating concise, natural responses.

Examples of supported interactions:

```text
Bakso di Gadog
Sundanese food in Bogor
Quiet coffee shops near Sudirman
Hotels in Sentul
Hospitals near me
Cari tempat makan dekat saya yang masih buka
Kasih lima pilihan
Yang murah yang mana?
Yang kedua aja
Jam berapa tempat tadi tutup?
```

The LLM is not treated as the factual source for place data. Google Places remains the source of truth.

---

### 2. Controlled AI orchestration

The backend separates language understanding from factual execution.

```text
User message + recent context
            ↓
Local Qwen semantic planning
            ↓
Validated backend orchestration
            ↓
Google Places search or place details
            ↓
Sanitized factual result
            ↓
Natural conversational response
            ↓
Stable API response
```

This division allows the assistant to feel natural while preventing the model from inventing:

- place names;
- ratings;
- opening status;
- exact addresses;
- exact menu prices;
- closing hours;
- distance or nearest-place claims;
- 24-hour availability.

When exact information is unavailable, the assistant responds honestly instead of fabricating data or failing with an invalid response.

---

### 3. Verified Google Places integration

The backend integrates with Google Places to retrieve verified place information such as:

- Google place ID;
- name;
- primary category;
- formatted address;
- rating;
- user rating count;
- opening status when available;
- price level when available;
- geographic coordinates;
- Google Maps and direction links.

Results from Google are normalized before being returned to the frontend.

The UI clearly identifies them as **Verified Places**.

---

### 4. Contextual place search and refinement

The assistant supports both new searches and contextual follow-ups.

Implemented behavior includes:

- category search;
- named-location search;
- current-location search;
- requested result count;
- open-now filtering;
- cheaper or affordable refinement;
- higher-rated alternatives;
- nearest-place handling;
- place selection by number or name;
- contextual questions about previous results;
- place-detail lookup;
- acknowledgements and general conversation.

Examples:

```text
User: Cari cafe yang masih buka dekat Stasiun Gubeng.
User: Kasih lima coba.
User: Yang murah yang mana?
User: Kisaran harga tiga tempat tadi berapa?
```

The assistant preserves relevant conversational context and avoids repeating a broad Google search when the answer can be resolved from the previous verified result set.

---

### 5. Geolocation intent handling

Browser geolocation is handled carefully.

Coordinates are only attached automatically when:

- the backend explicitly indicates that location is required; and
- a valid pending place-search request exists.

The application does not turn a general message such as `hi` into a generic location search.

When the user activates location without an active place request, the assistant asks:

```text
What would you like to find near you?
```

or, when Indonesian is appropriate:

```text
Mau mencari tempat apa di sekitar lokasi Anda?
```

Additional behavior:

- raw coordinates are not displayed;
- coordinates are not persistently stored;
- denied and unavailable permission states are handled;
- New Chat clears pending geolocation state.

---

### 6. Place cards and map synchronization

Verified backend results are the source of truth for the map.

When places are returned:

- the first verified place is selected initially;
- the inline map uses the selected place's `place_id`;
- Google Maps Embed uses **place mode**, not a broad search iframe;
- selecting a result card updates the exact place shown on the map;
- selecting a marker updates the matching place card;
- result indexes match map marker indexes;
- external Google Maps and Directions actions remain available.

This prevents unrelated Google search results from appearing as if they were part of the backend's verified response.

---

### 7. Interactive and accessible frontend

The Next.js frontend was designed as a focused conversational product interface.

Implemented UX details include:

- responsive chat layout;
- suggested place prompts;
- verified result cards;
- clear selected state;
- keyboard-selectable cards;
- visible hover and focus feedback;
- result index badges;
- synchronized card and marker selection;
- inline selected-place map;
- expanded multi-place map;
- accessible labels;
- separate in-app and external map actions;
- compact loading and error states;
- New Chat state reset.

The visual design was kept intentional and product-focused rather than resembling a default administration template.

---

## Technology Stack

### Frontend

- Next.js
- React
- TypeScript
- Google Maps Embed integration
- Google Maps interactive map integration
- Browser Geolocation API
- Responsive component-based UI

### Backend

- Python
- FastAPI
- Pydantic
- Google Places API
- Ollama HTTP integration
- Qwen local model
- Structured service and schema layers

### Infrastructure

- Docker
- Docker Compose
- Separate frontend and backend images
- Root-level orchestration
- Environment-based configuration

---

## Docker Architecture

The frontend and backend are built as separate Docker images and orchestrated through a single root-level Compose configuration.

```text
Root Docker Compose
├── Web service
│   └── Next.js image and runtime
└── API service
    └── FastAPI image and runtime
```

This was intentional.

Each service keeps its own:

- runtime;
- dependencies;
- build lifecycle;
- environment configuration;
- logs;
- restart behavior;
- deployment boundary.

The root Compose file provides a reproducible local workflow and a clear path toward independent deployment or future infrastructure expansion.

Typical startup flow:

```bash
docker compose up --build
```

The exact environment variables and commands are documented in the repository setup instructions.

---

## API Design

The frontend communicates with the FastAPI backend through a stable chat endpoint.

Representative response shape:

```json
{
  "message": "I found five open gas stations near your current location.",
  "intent": "place_search",
  "requires_location": false,
  "search_query": "gas station near current location",
  "places": [],
  "context": {}
}
```

Internal LLM planner output is validated and is not exposed directly to the client.

Public response intents remain stable even though the internal orchestration can distinguish between:

- new search;
- refinement;
- contextual answer;
- place details;
- selection;
- clarification;
- acknowledgement;
- general conversation;
- unsupported request.

---

## Security and Google API Practices

The implementation follows several defensive practices.

### Secret separation

- secrets are loaded through environment variables;
- `.env` files are excluded from source control;
- `.env.example` documents required configuration without credentials;
- API keys are not hardcoded into application source;
- backend credentials remain server-side;
- client-exposed Google keys are limited to APIs intended for browser use.

### Recommended Google Cloud restrictions

The repository documentation recommends configuring:

- HTTP referrer restrictions for browser keys;
- IP or server restrictions where applicable;
- API-level restrictions;
- Places API access only for backend credentials;
- Maps Embed or Maps JavaScript access only for the appropriate frontend key;
- daily quota and budget alerts;
- billing alerts;
- key rotation if a key is exposed.

### Runtime safety

- outbound requests use controlled parameters;
- unsupported Google fields are not forwarded;
- request timeouts are used;
- upstream failures are mapped to controlled API responses;
- raw upstream errors and secrets are not returned to the frontend;
- exact prices and opening claims are not invented.

---

## Price and Availability Handling

Google Places may provide categorical price information, but it does not guarantee exact menu prices.

Therefore:

- a request such as `budget 25 ribu` is treated as a user preference;
- categorical affordability can be used when available;
- the assistant does not guarantee that an item costs exactly Rp25,000;
- unsupported fields such as exact price, currency filters, or arbitrary budget values are not sent to Google.

Similarly:

- `open now` only includes places verified as currently open;
- unknown hours are not presented as open;
- `open 24 hours` is not inferred from `open_now`;
- verified opening-hours data is required for a 24-hour claim.

---

## Error Handling and Graceful Fallbacks

A valid conversational request should not fail only because the LLM returns malformed structured output.

The application includes controlled fallbacks for:

- invalid planner output;
- invalid natural-response output;
- missing optional Google fields;
- unavailable exact prices;
- unavailable closing times;
- no verified 24-hour result;
- unsupported factual detail;
- geolocation denial;
- Google upstream errors;
- local Ollama unavailability.

Examples of safe behavior:

```text
Google Maps only provides a general price category for these places,
not exact menu prices.
```

```text
I found the place, but Google Maps does not currently provide a verified closing time.
```

These cases return an honest response rather than an invented answer.

---

## Stateless Context Model

The backend remains stateless.

The frontend sends recent conversation history and a compact structured context containing only information needed for follow-up resolution.

Context may include:

- last search category;
- last location;
- previous place IDs;
- lightweight previous place references;
- selected result;
- recent intent.

The context is bounded to avoid unnecessary payload growth.

Client-provided context is used for conversational reference resolution. Factual detail is revalidated through Google when appropriate.

---

## Assumptions

1. **Google Places is the factual source of truth.**  
   The local LLM interprets language and produces responses but does not independently verify business information.

2. **The application is a local-first prototype.**  
   Ollama and the selected Qwen model are expected to be installed or available through the documented environment.

3. **The backend is stateless.**  
   Conversation context is sent by the frontend rather than stored in a database.

4. **Current location is session-only.**  
   Browser coordinates are not persistently stored.

5. **Exact menu pricing is outside the reliable Google Places dataset.**  
   Price levels are treated as approximate categories.

6. **Opening-hour data may be incomplete.**  
   Missing availability is communicated clearly.

7. **Inline maps show the exact selected verified place.**  
   The expanded map is used for interaction across multiple verified results.

8. **A browser-exposed map key must be restricted.**  
   Public browser keys are not assumed to be secret and must be protected with referrer and API restrictions.

9. **AI-assisted coding was used responsibly.**  
   Architecture selection, integration decisions, testing, debugging, security review, and final validation remained part of the engineering process.

---

## Engineering Decisions

### Why Qwen and Ollama?

- fully local inference;
- no external LLM dependency;
- simple reproducible HTTP integration;
- appropriate for multilingual conversational understanding;
- aligns directly with the local-LLM requirement.

### Why FastAPI?

- strong request and response validation with Pydantic;
- clean async integration with Ollama and Google APIs;
- concise service-layer organization;
- straightforward testing;
- automatic API documentation.

### Why separate AI planning from Google execution?

The LLM is strong at interpreting ambiguous language, while backend code is more reliable for:

- legal API parameters;
- factual validation;
- filtering;
- distance calculations;
- timeouts;
- retries;
- error mapping.

This produces a more natural assistant without sacrificing correctness.

### Why separate Docker images?

Next.js and FastAPI have different runtimes and dependencies. Separate images preserve clean service boundaries and avoid a single oversized container.

### Why use verified place IDs for the map?

A generic map-search iframe can display results not returned by the backend. Using the selected verified `place_id` keeps the map synchronized with the assistant's actual response.

---

## Validation Performed

The implementation was exercised through realistic conversational flows, including:

### Direct search

```text
Bakso di Gadog
Hotels in Sentul
Pom bensin
```

### Location-required flow

```text
User activates current location
Assistant asks what to find
User enters a place category
Coordinates are attached only to that valid request
```

### Open-now flow

```text
Cari tempat makan dekat saya yang masih buka only ya
```

### Refinement flow

```text
Kasih lima pilihan
Yang murah yang mana?
```

### Contextual question

```text
Kisaran harga tiga tempat tadi berapa?
Yang kedua namanya apa?
```

### Place selection and map synchronization

```text
Select result card 2
Map changes to the exact place ID for result 2
```

### General conversation

```text
Makasih
Bisa bahasa Indonesia?
```

### Map actions

- view selected place inline;
- expand interactive map;
- select markers;
- open Google Maps;
- open directions.

Automated checks are included in the repository where applicable. Real Google and Ollama integrations should remain mocked in automated tests to avoid network dependency and quota usage.

---

## Suggested Reviewer Setup

1. Copy the environment example files.
2. Add the required Google API keys.
3. Ensure the configured Ollama model is available.
4. Start the services from the repository root.

```bash
docker compose up --build
```

Alternatively, run the frontend and backend independently using the commands documented in their respective directories.

---

## Project Outcome

The original test asks for a local LLM that can find places and output Google Maps.

The completed implementation delivers that core requirement and extends it into a more complete product prototype with:

- local conversational AI;
- verified Google place grounding;
- safe contextual orchestration;
- current-location support;
- map and card synchronization;
- embedded and external directions;
- graceful fallbacks;
- responsive UX;
- service separation;
- reproducible Docker orchestration;
- documented assumptions and security practices.

The goal was not only to make the happy path work, but to demonstrate how I approach ambiguity, integration boundaries, product behavior, API safety, failure modes, and developer experience in a real-world engineering task.
