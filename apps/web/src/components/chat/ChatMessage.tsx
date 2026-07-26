"use client";

import React from "react";
import { ChatMessage as ChatMessageType } from "@/types/chat";
import { PlaceCard } from "../places/PlaceCard";
import { LocationClarification } from "./LocationClarification";
import { InlineEmbeddedMap } from "../map/InlineEmbeddedMap";

interface ChatMessageProps {
  message: ChatMessageType;
  selectedPlaceId: string | null;
  activeMessageIdWithPlaces: string | null;
  onSelectPlace: (placeId: string) => void;
  onSelectMessagePlaces: (messageId: string) => void;
  onLocationSelected: (coords: { lat: number; lng: number }) => void;
  onExpandMap: (messageId: string) => void;
  onRetry?: (messageId: string) => void;
}

export function ChatMessage({
  message,
  selectedPlaceId,
  activeMessageIdWithPlaces,
  onSelectPlace,
  onSelectMessagePlaces,
  onLocationSelected,
  onExpandMap,
  onRetry,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  // Standard User message bubble with optional location confirmation chip
  if (isUser) {
    if (message.isLocationConfirmation && message.content === "Using my current location") {
      return (
        <div className="animate-fade-in-up flex justify-center w-full my-1">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200/80 bg-zinc-100/90 px-3.5 py-1 text-xs font-semibold text-zinc-600 shadow-2xs dark:border-zinc-800/80 dark:bg-zinc-800/80 dark:text-zinc-300">
            <span className="text-xs">📍</span>
            <span>Using your current location</span>
          </div>
        </div>
      );
    }

    return (
      <div className="animate-fade-in-up flex justify-end w-full">
        <div className="flex max-w-[85%] sm:max-w-[75%] flex-col items-end gap-1">
          <div className="rounded-2xl rounded-tr-xs bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 px-4 py-2.5 text-xs sm:text-sm font-medium text-white shadow-md shadow-blue-500/15">
            {message.content}
          </div>
          {message.isLocationConfirmation && (
            <div className="inline-flex items-center gap-1 text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 pr-1">
              <span>📍</span>
              <span>GPS location attached</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Assistant message
  const hasPlaces = message.places && message.places.length > 0;
  const isMapActiveForThisMsg = activeMessageIdWithPlaces === message.id;
  const isError = message.status === "error";

  const handlePlaceCardSelect = (placeId: string) => {
    onSelectMessagePlaces(message.id);
    onSelectPlace(placeId);
  };

  return (
    <div className="animate-fade-in-up flex w-full items-start gap-3">
      {/* AI Avatar */}
      <div className="relative flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 font-bold text-white text-xs shadow-md shadow-blue-500/20 ring-2 ring-white dark:ring-zinc-950">
        AI
      </div>

      <div className="flex flex-1 flex-col gap-2 max-w-[92%] sm:max-w-[95%]">
        {/* Header & Badges */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-zinc-900 dark:text-zinc-100">
            Pico
          </span>

          {message.intent && !isError && (
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                message.intent === "place_search" ||
                message.intent === "place_refinement"
                  ? "bg-blue-50 text-blue-700 ring-1 ring-blue-600/20 dark:bg-blue-950/60 dark:text-blue-300 dark:ring-blue-500/30"
                  : message.intent === "general"
                  ? "bg-zinc-100 text-zinc-600 ring-1 ring-zinc-500/20 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700"
                  : "bg-amber-50 text-amber-700 ring-1 ring-amber-600/20 dark:bg-amber-950/60 dark:text-amber-300 dark:ring-amber-500/30"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  message.intent === "place_search" ||
                  message.intent === "place_refinement"
                    ? "bg-blue-500"
                    : message.intent === "general"
                    ? "bg-zinc-400"
                    : "bg-amber-500"
                }`}
              />
              {message.intent === "place_search"
                ? "Place Search"
                : message.intent === "place_refinement"
                ? "Refined Search"
                : message.intent === "general"
                ? "General"
                : "Unsupported"}
            </span>
          )}
        </div>

        {/* Response Content Bubble / Error Presentation */}
        {isError ? (
          <div
            role="alert"
            aria-live="assertive"
            className="flex items-center justify-between gap-3 rounded-2xl rounded-tl-xs border border-rose-200 bg-rose-50/80 p-3.5 text-xs text-rose-800 shadow-xs dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200"
          >
            <span className="font-medium">
              {message.errorMessage || message.content || "Could not connect to the local backend."}
            </span>
            {onRetry && (
              <button
                type="button"
                onClick={() => onRetry(message.id)}
                className="inline-flex flex-shrink-0 items-center gap-1 rounded-xl bg-rose-600 px-3 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-rose-700 transition-all active:scale-95 focus:outline-none focus:ring-2 focus:ring-rose-500/30"
              >
                <svg
                  className="h-3.5 w-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Try again
              </button>
            )}
          </div>
        ) : (
          <div className="rounded-2xl rounded-tl-xs border border-zinc-200/80 bg-white p-4 text-xs sm:text-sm leading-relaxed text-zinc-800 shadow-xs dark:border-zinc-800/80 dark:bg-zinc-900 dark:text-zinc-200">
            {message.content}
          </div>
        )}

        {/* Location Clarification Widget */}
        {message.requiresLocation && !isError && (
          <LocationClarification
            onLocationSelected={onLocationSelected}
            disabled={message.status === "sending"}
          />
        )}

        {/* Attached Verified Places & Inline Google Map */}
        {hasPlaces && message.places && !isError && (
          <div className="mt-2 flex flex-col gap-3">
            <div className="flex items-center justify-between pt-1">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                Verified Places ({message.places.length})
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2.5">
              {message.places.map((place, idx) => (
                <PlaceCard
                  key={place.place_id}
                  place={place}
                  index={idx + 1}
                  isSelected={
                    isMapActiveForThisMsg && selectedPlaceId === place.place_id
                  }
                  onSelect={handlePlaceCardSelect}
                />
              ))}
            </div>

            {/* Inline Embedded Google Map Response */}
            <InlineEmbeddedMap
              searchQuery={message.searchQuery}
              places={message.places}
              selectedPlaceId={
                isMapActiveForThisMsg ? selectedPlaceId : message.places[0]?.place_id || null
              }
              onExpandMap={() => onExpandMap(message.id)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
