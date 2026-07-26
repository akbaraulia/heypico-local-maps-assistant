import { API_BASE_URL } from "./constants";
import { normalizeSearchContext } from "./chat-history";
import { ApiError, ApiErrorPayload } from "@/types/api";
import { ChatRequest, ChatResponse } from "@/types/chat";

const CHAT_STATUS_ERROR_MESSAGES: Record<number, string> = {
  422: "Please enter a valid message.",
  429: "Too many requests. Wait a moment and try again.",
  502: "The local assistant could not process that request.",
  503: "The local assistant is currently unavailable. Make sure Ollama and the backend are running.",
  504: "The local assistant took too long to respond.",
};

const VALID_INTENTS = new Set([
  "place_search",
  "place_refinement",
  "general",
  "unsupported",
]);

export async function sendChatMessage(
  payload: ChatRequest,
  signal?: AbortSignal
): Promise<ChatResponse> {
  const trimmed = payload.message.trim();
  if (!trimmed) {
    throw new ApiError("Please enter a valid message.", 422, "empty_message");
  }

  const normalizedBaseUrl = API_BASE_URL.replace(/\/+$/, "");
  const url = `${normalizedBaseUrl}/api/chat`;

  const body: Record<string, unknown> = {
    message: trimmed,
    user_lat: payload.user_lat ?? null,
    user_lng: payload.user_lng ?? null,
  };

  if (Array.isArray(payload.history) && payload.history.length > 0) {
    body.history = payload.history;
  }

  if (payload.context && typeof payload.context === "object") {
    body.context = payload.context;
  }

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
      signal,
    });

    if (!response.ok) {
      let code: string | undefined;
      let serverDetail: string | undefined;

      try {
        const errorData: ApiErrorPayload = await response.json();
        code = errorData.error?.code;
        serverDetail = errorData.error?.message || errorData.detail;
      } catch {
        // Response body was not JSON or unparseable
      }

      const friendlyMessage =
        CHAT_STATUS_ERROR_MESSAGES[response.status] ||
        serverDetail ||
        "The local assistant could not process that request.";

      throw new ApiError(friendlyMessage, response.status, code);
    }

    const data = await response.json();

    if (
      !data ||
      typeof data.message !== "string" ||
      typeof data.intent !== "string" ||
      !VALID_INTENTS.has(data.intent) ||
      typeof data.requires_location !== "boolean" ||
      !Array.isArray(data.places)
    ) {
      throw new ApiError(
        "The local assistant returned an invalid response structure.",
        502,
        "malformed_response"
      );
    }

    const normalizedContext =
      data.context !== undefined && data.context !== null
        ? normalizeSearchContext(data.context)
        : data.context === null
        ? null
        : undefined;

    return {
      message: data.message,
      intent: data.intent as ChatResponse["intent"],
      requires_location: data.requires_location,
      search_query:
        typeof data.search_query === "string" ? data.search_query : null,
      places: data.places,
      context: normalizedContext,
    };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError(
      "Could not connect to the local backend. Make sure the backend server is running.",
      503,
      "network_error"
    );
  }
}
