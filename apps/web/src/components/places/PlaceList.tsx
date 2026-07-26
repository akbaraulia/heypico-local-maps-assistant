"use client";

import React from "react";
import { Place } from "@/types/place";
import { PlaceCard } from "./PlaceCard";

interface PlaceListProps {
  places: Place[];
  query: string;
  selectedPlaceId: string | null;
  onSelectPlace: (placeId: string) => void;
}

export function PlaceList({
  places,
  query,
  selectedPlaceId,
  onSelectPlace,
}: PlaceListProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-zinc-200 pb-3 dark:border-zinc-800">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Search Results
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Found {places.length} {places.length === 1 ? "place" : "places"} for &ldquo;
            <span className="font-medium text-zinc-700 dark:text-zinc-300">
              {query}
            </span>
            &rdquo;
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {places.map((place) => (
          <PlaceCard
            key={place.place_id}
            place={place}
            isSelected={selectedPlaceId === place.place_id}
            onSelect={onSelectPlace}
          />
        ))}
      </div>
    </div>
  );
}
