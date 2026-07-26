# Pico Local Maps Assistant - Frontend (Phase 2 & Phase 2.2)

Pico Local Maps Assistant is a conversational local place-discovery web application built with Next.js App Router, TypeScript, and Tailwind CSS. It communicates with the FastAPI backend service (`POST /api/chat`) which orchestrates local LLM intent extraction (via Ollama `qwen3:4b`) and Google Places data retrieval.

---

## 🎯 Scope & UX Architecture

The application is designed as a **centered chatbot experience** with embedded Google Maps responses:
- **Centered Chatbot UX (Default)**: Clean, single-column chatbot experience (centered max-width ~800–960px). Conversation history displays user and assistant message bubbles, typing indicators, location clarification widgets, and prompt suggestions.
- **Inline Embedded Google Maps**: When an assistant message returns places (`intent === "place_search"` or `"place_refinement"`), an embedded Google Map iframe (using Google Maps Embed API) renders directly inside the assistant message bubble along with verified place cards.
- **Interactive Card Selection**: Clicking a place card highlights the card and updates the inline Google Maps Embed iframe (using `q=place_id:<PLACE_ID>`).
- **Expanded Map Mode**: Clicking **"Expand map"** on any place-search assistant response activates side-by-side mode (desktop: Chat 42%, Interactive JS Map 58%; mobile: full view modal/overlay). Clicking **"Close map"** restores the standard centered chatbot layout while preserving chat history and selected places.
- **Location Clarification**: Detects `requires_location = true` and presents an explicit "Use my current location" action button or guidance to type a city/landmark.
- **Browser Geolocation**: Geolocation API is called **only** after explicit user click on "Use my current location".
- **Safe Fallback**: Displays a clear setup notice when `NEXT_PUBLIC_GOOGLE_MAPS_EMBED_API_KEY` is missing without crashing the application.

---

## 🔄 Conversational History & Structured Search Context (Phase 2.2)

- **History Integration**: The frontend automatically sends up to 10 recent eligible user/assistant text messages in `request.history`. Initial welcome messages, typing placeholders, error alerts, and unsubmitted prompt labels are filtered out.
- **Structured Search Context**: The frontend retains the latest backend-provided structured search context (`SearchContext`) in memory and sends it in `request.context`.
- **Refinement Intent**: Supports `intent === "place_refinement"` responses alongside `place_search`.
- **Context Lifecycle**: Context is preserved across general chat and location clarification responses, and is reset only when the chat is explicitly cleared or the page reloaded. Context is not persisted in `localStorage`.
- **Backend Responsibility**: The backend remains authoritative for interpreting follow-up refinements (e.g. price, rating, category filters). The frontend does not infer or fabricate search context.
- **Backward Compatibility**: Fully compatible with older backend responses that omit the `context` field. Full follow-up refinement behavior requires Backend Phase 2.1.

---

## 📋 Prerequisites

- **Node.js**: v18.17+ or v20+
- **npm**: v9+
- **Backend Service**: Running `apps/api` on `http://localhost:8000`
- **Ollama**: Local Ollama service running with `qwen3:4b` model pulled (`ollama pull qwen3:4b`)
- **Google Maps API Key**: Browser key enabled for Google Maps Embed API & Google Maps JavaScript API (restricted by HTTP referrer).

---

## 🔑 Environment Variables

Copy `.env.example` to `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_MAPS_EMBED_API_KEY=
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=
```

---

## 🚀 Setup & Execution

### Windows PowerShell Setup

```powershell
cd C:\Coding\heypico-local-maps-assistant\apps\web

npm install

Copy-Item .env.example .env.local

npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 💬 Example Prompts

Try asking the assistant:
- **Indonesian explicit location**: `Cari restoran Sunda di Bogor`
- **Follow-up refinement**: `yang budget menu nya agak murah dimana?`
- **English explicit area**: `Find coffee shops near Sudirman Jakarta`
- **Missing location query**: `Cari rumah sakit terdekat` *(triggers location clarification)*
- **Location follow-up**: `Bogor` or click `Use my current location`
- **General chat**: `Halo, kamu bisa apa?`
- **Specific place category**: `Hotels near Sentul` or `ATM BCA near Grand Indonesia`

---

## 🏗️ Folder Structure

```
apps/web/
├── public/
├── src/
│   ├── app/
│   │   ├── globals.css              # Tailwind CSS styles & font variables
│   │   ├── layout.tsx               # Root layout and metadata
│   │   └── page.tsx                 # Main page with Suspense wrapper
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatComposer.tsx     # Textarea input with length validation & Shift+Enter
│   │   │   ├── ChatMessage.tsx      # User/assistant message bubbles with inline maps & cards
│   │   │   ├── ChatPanel.tsx        # Scrollable conversation container
│   │   │   ├── LocationClarification.tsx # Location request widget & geolocation button
│   │   │   ├── SuggestionChips.tsx  # Clickable query prompt chips
│   │   │   ├── TypingIndicator.tsx  # Animated assistant thinking indicator
│   │   │   └── WelcomeMessage.tsx   # Initial greeting component
│   │   ├── layout/
│   │   │   ├── AppHeader.tsx        # Branding & status badges header
│   │   │   └── MainLayout.tsx       # Centered chatbot layout & expanded map layout
│   │   ├── map/
│   │   │   ├── InlineEmbeddedMap.tsx # Google Maps Embed API iframe component
│   │   │   ├── MapFallback.tsx      # Notice when Maps API key is missing
│   │   │   ├── PlacesMap.tsx        # Google Maps JS API loader & markers
│   │   │   └── SelectedPlaceOverlay.tsx # Selected place summary card overlay
│   │   └── places/
│   │       └── PlaceCard.tsx        # Individual place result card component
│   ├── hooks/
│   │   ├── useBrowserLocation.ts    # Safe browser geolocation hook
│   │   └── useChat.ts               # Chat state, message history & context hook
│   ├── lib/
│   │   ├── api.ts                   # Fetch client for POST /api/chat & error mapping
│   │   ├── chat-history.ts          # History builder & context normalizer utilities
│   │   ├── constants.ts             # Default centers & example queries
│   │   └── formatters.ts            # Rating, review count & status formatters
│   └── types/
│       ├── api.ts                   # API payload types
│       ├── chat.ts                  # Chat message, request/response & context interfaces
│       └── place.ts                 # Normalized Place model interface
├── .env.example
├── package.json
└── README.md
```

---

## 🧪 Testing & Build Commands

```bash
# Run ESLint check
npm run lint

# Build production bundle
npm run build
```

---

## 📋 Manual Test Checklist

1. Default view loads as a centered chatbot experience without permanent split-screen map.
2. Initial welcome message renders with suggestion chips.
3. Query `Cari restoran Sunda di Bogor` renders response text, place cards, and inline embedded map.
4. History payload sends up to 10 previous eligible text messages without repeating the outgoing user message.
5. Follow-up `yang budget menu nya agak murah dimana?` sends `history` array and `context` object in `POST /api/chat`.
6. `place_refinement` responses render place cards and inline map identically to `place_search`.
7. General message `Halo, kamu bisa apa?` sends `history` and `context` while preserving `latestSearchContext`.
8. Missing `context` field in backend response does not crash UI and preserves previous context.
9. Click "Clear Chat" resets messages and clears `latestSearchContext`.
10. Page refresh clears in-memory context without touching `localStorage`.
