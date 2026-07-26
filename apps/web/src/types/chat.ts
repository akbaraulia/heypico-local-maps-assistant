import { Place } from "./place";

export type ChatRole = "user" | "assistant";

export type ChatIntent =
  | "place_search"
  | "place_refinement"
  | "general"
  | "unsupported";

export type ChatMessageStatus = "sending" | "complete" | "error";

export type ChatHistoryRole = "user" | "assistant";

export interface ChatHistoryMessage {
  role: ChatHistoryRole;
  content: string;
}

export interface SearchContext {
  last_intent?: ChatIntent | null;
  last_search_terms?: string | null;
  last_location?: string | null;
  last_search_query?: string | null;
  last_place_ids?: string[];
  reference_lat?: number | null;
  reference_lng?: number | null;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
  intent?: ChatIntent;
  requiresLocation?: boolean;
  searchQuery?: string | null;
  places?: Place[];
  context?: SearchContext | null;
  status?: ChatMessageStatus;
  errorMessage?: string;
  isLocationConfirmation?: boolean;
}

export interface ChatRequest {
  message: string;
  user_lat?: number | null;
  user_lng?: number | null;
  history?: ChatHistoryMessage[];
  context?: SearchContext | null;
}

export interface ChatResponse {
  message: string;
  intent: ChatIntent;
  requires_location: boolean;
  search_query: string | null;
  places: Place[];
  context?: SearchContext | null;
}
