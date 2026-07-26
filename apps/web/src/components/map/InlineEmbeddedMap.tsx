"use client";

import React from "react";
import { Place } from "@/types/place";
import { GOOGLE_MAPS_EMBED_API_KEY } from "@/lib/constants";

interface InlineEmbeddedMapProps {
  searchQuery?: string | null;
  places: Place[];
  selectedPlaceId: string | null;
  onExpandMap: () => void;
}

export function InlineEmbeddedMap({
  searchQuery,
  places,
  selectedPlaceId,
  onExpandMap,
}: InlineEmbeddedMapProps) {
  if (!GOOGLE_MAPS_EMBED_API_KEY) {
    return (
      <div className="mt-3 flex flex-col items-center justify-center rounded-2xl border border-dashed border-amber-300/80 bg-amber-50/50 p-4 text-center dark:border-amber-900/50 dark:bg-amber-950/30">
        <p className="text-xs font-semibold text-amber-800 dark:text-amber-300">
          Add NEXT_PUBLIC_GOOGLE_MAPS_EMBED_API_KEY to display the embedded map.
        </p>
      </div>
    );
  }

  const hasPlaces = places && places.length > 0;
  const targetPlace = hasPlaces
    ? places.find((p) => p.place_id === selectedPlaceId) || places[0]
    : null;

  const baseUrl = "https://www.google.com/maps/embed/v1";
  const params = new URLSearchParams({
    key: GOOGLE_MAPS_EMBED_API_KEY,
  });

  let embedEndpoint = "place";
  let externalMapsUrl = "https://www.google.com/maps";
  let statusLabel = "Viewing place on the map";

  if (targetPlace && targetPlace.place_id) {
    embedEndpoint = "place";
    params.set("q", `place_id:${targetPlace.place_id}`);
    externalMapsUrl = targetPlace.google_maps_url;
    statusLabel = `Viewing ${targetPlace.name} on the map`;
  } else if (
    targetPlace &&
    typeof targetPlace.lat === "number" &&
    typeof targetPlace.lng === "number"
  ) {
    embedEndpoint = "view";
    params.set("center", `${targetPlace.lat},${targetPlace.lng}`);
    params.set("zoom", "15");
    statusLabel = `Viewing ${targetPlace.name} on the map`;
  } else if (searchQuery && searchQuery.trim() && !hasPlaces) {
    embedEndpoint = "search";
    params.set("q", searchQuery.trim());
    externalMapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
      searchQuery.trim()
    )}`;
    statusLabel = `Viewing search query "${searchQuery.trim()}" on the map`;
  }

  const iframeSrc = `${baseUrl}/${embedEndpoint}?${params.toString()}`;

  return (
    <div className="mt-3 flex flex-col gap-2.5">
      {/* Subtle Selected Result Status Label */}
      <div className="flex items-center justify-between text-[11px] font-medium text-zinc-500 dark:text-zinc-400 px-0.5">
        <span className="inline-flex items-center gap-1.5 truncate">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-500 flex-shrink-0" />
          <span className="truncate">{statusLabel}</span>
        </span>
        {hasPlaces && places.length > 1 && (
          <span className="hidden sm:inline text-[10px] text-zinc-400 dark:text-zinc-500 font-normal">
            Select another place to update the map.
          </span>
        )}
      </div>

      {/* Map Container */}
      <div className="relative overflow-hidden rounded-2xl border border-zinc-200/80 bg-zinc-100 shadow-xs dark:border-zinc-800/80 dark:bg-zinc-900">
        <iframe
          title="Google Maps Result"
          src={iframeSrc}
          className="h-[260px] w-full sm:h-[300px] border-0"
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          allowFullScreen
        />
      </div>

      {/* Action Controls */}
      <div className="flex items-center justify-between text-xs pt-0.5">
        <button
          type="button"
          onClick={onExpandMap}
          className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs px-3.5 py-2 shadow-md shadow-blue-500/20 transition-all active:scale-95 border border-blue-500/30 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
        >
          <svg
            className="h-3.5 w-3.5 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
            />
          </svg>
          Expand interactive map
        </button>

        <a
          href={externalMapsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 font-semibold text-zinc-600 hover:text-blue-600 dark:text-zinc-400 dark:hover:text-blue-400 transition-colors"
        >
          Open in Google Maps &rarr;
        </a>
      </div>
    </div>
  );
}
