"use client";

import { useCallback, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api";
import { buildChatHistory } from "@/lib/chat-history";
import { ChatMessage, ChatRequest, SearchContext } from "@/types/chat";
import { Place } from "@/types/place";

const INITIAL_WELCOME_MESSAGE: ChatMessage = {
  id: "msg-welcome-01",
  role: "assistant",
  content:
    "Hi! Ask me where to eat, visit, shop, stay, or explore. I’ll use the local language model to understand your request and Google Maps data to find verified places.",
  createdAt: Date.now(),
  status: "complete",
};

export interface UseChatReturn {
  messages: ChatMessage[];
  isSending: boolean;
  activePlaces: Place[];
  selectedPlaceId: string | null;
  activeMessageIdWithPlaces: string | null;
  pendingClarificationQuery: string | null;
  latestSearchContext: SearchContext | null;
  isMapExpanded: boolean;
  sendMessage: (
    text: string,
    coords?: { lat: number; lng: number }
  ) => Promise<void>;
  retryMessage: (assistantMsgId: string) => Promise<void>;
  selectPlace: (placeId: string | null) => void;
  selectMessagePlaces: (messageId: string) => void;
  expandMap: (messageId?: string) => void;
  closeMap: () => void;
  clearChatHistory: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([
    INITIAL_WELCOME_MESSAGE,
  ]);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [activePlaces, setActivePlaces] = useState<Place[]>([]);
  const [selectedPlaceId, setSelectedPlaceId] = useState<string | null>(null);
  const [activeMessageIdWithPlaces, setActiveMessageIdWithPlaces] = useState<
    string | null
  >(null);
  const [pendingClarificationQuery, setPendingClarificationQuery] = useState<
    string | null
  >(null);
  const [latestSearchContext, setLatestSearchContext] =
    useState<SearchContext | null>(null);
  const [isMapExpanded, setIsMapExpanded] = useState<boolean>(false);
  const [sessionUserCoords, setSessionUserCoords] = useState<{
    lat: number;
    lng: number;
  } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const performSend = useCallback(
    async (
      displayedText: string,
      backendText: string,
      currentHistory: ReturnType<typeof buildChatHistory>,
      currentContext: SearchContext | null,
      coords?: { lat: number; lng: number }
    ) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      const userMsgId = `user-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;
      const assistantMsgId = `asst-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`;

      const userMessage: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: displayedText,
        createdAt: Date.now(),
        status: "complete",
        isLocationConfirmation: Boolean(coords),
      };

      const pendingAssistantMessage: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        createdAt: Date.now() + 1,
        status: "sending",
      };

      setMessages((prev) => [...prev, userMessage, pendingAssistantMessage]);
      setIsSending(true);

      const requestPayload: ChatRequest = {
        message: backendText,
        user_lat: coords ? coords.lat : null,
        user_lng: coords ? coords.lng : null,
        history: currentHistory.length > 0 ? currentHistory : undefined,
        context: currentContext || undefined,
      };

      try {
        const response = await sendChatMessage(
          requestPayload,
          controller.signal
        );

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: response.message,
                  intent: response.intent,
                  requiresLocation: response.requires_location,
                  searchQuery: response.search_query,
                  places: response.places,
                  context: response.context,
                  status: "complete",
                }
              : msg
          )
        );

        if (response.context !== undefined) {
          setLatestSearchContext(response.context);
        }

        if (response.requires_location) {
          setPendingClarificationQuery(backendText);
        } else {
          setPendingClarificationQuery(null);

          if (
            response.intent === "place_search" ||
            response.intent === "place_refinement"
          ) {
            setActivePlaces(response.places);
            setActiveMessageIdWithPlaces(assistantMsgId);
            if (response.places && response.places.length > 0) {
              setSelectedPlaceId(response.places[0].place_id);
            } else {
              setSelectedPlaceId(null);
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        const errorMessage =
          err instanceof Error
            ? err.message
            : "An unexpected error occurred. Please try again.";

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: errorMessage,
                  status: "error",
                  errorMessage,
                }
              : msg
          )
        );
      } finally {
        setIsSending(false);
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    []
  );

  const sendMessage = useCallback(
    async (text: string, coords?: { lat: number; lng: number }) => {
      // If explicit coords passed (e.g. Near Me button), update session coords
      let activeCoords = coords;
      if (coords) {
        setSessionUserCoords(coords);
      } else if (sessionUserCoords) {
        activeCoords = sessionUserCoords;
      } else if (
        latestSearchContext?.reference_lat != null &&
        latestSearchContext?.reference_lng != null
      ) {
        activeCoords = {
          lat: latestSearchContext.reference_lat,
          lng: latestSearchContext.reference_lng,
        };
      }

      const history = buildChatHistory(messages);
      const currentContext = latestSearchContext;

      const lastAssistantMsg = [...messages]
        .reverse()
        .find((m) => m.role === "assistant");

      const canRetryWithLocation =
        Boolean(pendingClarificationQuery) &&
        Boolean(lastAssistantMsg?.requiresLocation);

      if (coords) {
        if (canRetryWithLocation && pendingClarificationQuery) {
          const queryToUse = pendingClarificationQuery;
          setPendingClarificationQuery(null);
          await performSend(
            text.trim() || "Using my current location",
            queryToUse,
            history,
            currentContext,
            coords
          );
        } else if (text.trim()) {
          // User typed a specific prompt AND clicked Near Me / attached location
          await performSend(
            text.trim(),
            text.trim(),
            history,
            currentContext,
            coords
          );
        } else {
          // Near Me clicked without a text prompt
          const isIndonesian =
            Boolean(text && /di|sekitar|dekat|cari/i.test(text)) ||
            messages.some((m) =>
              /di|sekitar|dekat|cari|halo|bisa|kamu/i.test(m.content)
            );

          const promptText = isIndonesian
            ? "Mau mencari tempat apa di sekitar lokasi Anda?"
            : "What would you like to find near you?";

          const userLocMsg: ChatMessage = {
            id: `user-${Date.now()}`,
            role: "user",
            content: "Using my current location",
            createdAt: Date.now(),
            status: "complete",
            isLocationConfirmation: true,
          };

          const asstPromptMsg: ChatMessage = {
            id: `asst-${Date.now() + 1}`,
            role: "assistant",
            content: promptText,
            createdAt: Date.now() + 2,
            status: "complete",
            intent: "general",
          };

          setMessages((prev) => [...prev, userLocMsg, asstPromptMsg]);
        }
        return;
      }

      const trimmed = text.trim();
      if (!trimmed) return;

      let backendText = trimmed;

      if (pendingClarificationQuery) {
        const lowerInput = trimmed.toLowerCase();
        if (
          lowerInput.startsWith("in ") ||
          lowerInput.startsWith("near ") ||
          lowerInput.startsWith("di ") ||
          lowerInput.startsWith("sekitar ")
        ) {
          backendText = `${pendingClarificationQuery} ${trimmed}`;
        } else {
          backendText = `${pendingClarificationQuery} in ${trimmed}`;
        }
      }

      await performSend(
        trimmed,
        backendText,
        history,
        currentContext,
        activeCoords || undefined
      );
    },
    [
      messages,
      latestSearchContext,
      pendingClarificationQuery,
      sessionUserCoords,
      performSend,
    ]
  );

  const retryMessage = useCallback(
    async (assistantMsgId: string) => {
      const index = messages.findIndex((m) => m.id === assistantMsgId);
      if (index <= 0) return;

      const userMsg = messages[index - 1];
      if (!userMsg || userMsg.role !== "user") return;

      setMessages((prev) =>
        prev.filter((m) => m.id !== assistantMsgId && m.id !== userMsg.id)
      );

      await sendMessage(userMsg.content);
    },
    [messages, sendMessage]
  );

  const selectPlace = useCallback((placeId: string | null) => {
    setSelectedPlaceId(placeId);
  }, []);

  const selectMessagePlaces = useCallback(
    (messageId: string) => {
      const msg = messages.find((m) => m.id === messageId);
      if (msg && msg.places && msg.places.length > 0) {
        setActivePlaces(msg.places);
        setActiveMessageIdWithPlaces(messageId);
        setSelectedPlaceId(msg.places[0].place_id);
      }
    },
    [messages]
  );

  const expandMap = useCallback(
    (messageId?: string) => {
      if (messageId) {
        selectMessagePlaces(messageId);
      }
      setIsMapExpanded(true);
    },
    [selectMessagePlaces]
  );

  const closeMap = useCallback(() => {
    setIsMapExpanded(false);
  }, []);

  const clearChatHistory = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setMessages([INITIAL_WELCOME_MESSAGE]);
    setIsSending(false);
    setActivePlaces([]);
    setSelectedPlaceId(null);
    setActiveMessageIdWithPlaces(null);
    setPendingClarificationQuery(null);
    setLatestSearchContext(null);
    setIsMapExpanded(false);
    setSessionUserCoords(null);
  }, []);

  return {
    messages,
    isSending,
    activePlaces,
    selectedPlaceId,
    activeMessageIdWithPlaces,
    pendingClarificationQuery,
    latestSearchContext,
    isMapExpanded,
    sendMessage,
    retryMessage,
    selectPlace,
    selectMessagePlaces,
    expandMap,
    closeMap,
    clearChatHistory,
  };
}
