"use client";

import React from "react";
import { Place } from "@/types/place";
import {
  formatOpenStatus,
  formatPrimaryType,
  formatRating,
  formatReviewCount,
} from "@/lib/formatters";

interface PlaceCardProps {
  place: Place;
  isSelected: boolean;
  onSelect: (placeId: string) => void;
  index?: number;
}

function formatPriceLevel(priceLevel: string | null | undefined): string | null {
  if (!priceLevel) return null;
  switch (priceLevel) {
    case "PRICE_LEVEL_FREE":
      return "Free";
    case "PRICE_LEVEL_INEXPENSIVE":
      return "$";
    case "PRICE_LEVEL_MODERATE":
      return "$$";
    case "PRICE_LEVEL_EXPENSIVE":
      return "$$$";
    case "PRICE_LEVEL_VERY_EXPENSIVE":
      return "$$$$";
    default:
      return null;
  }
}

export function PlaceCard({ place, isSelected, onSelect, index }: PlaceCardProps) {
  const openStatus = formatOpenStatus(place.open_now);
  const formattedType = formatPrimaryType(place.primary_type);
  const formattedRating = formatRating(place.rating);
  const formattedReviews = formatReviewCount(place.user_rating_count);
  const priceSymbol = formatPriceLevel(place.price_level);

  const handleClick = () => {
    onSelect(place.place_id);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect(place.place_id);
    }
  };

  return (
    <div
      tabIndex={0}
      role="button"
      aria-pressed={isSelected}
      aria-label={`Place result ${index || ""}: ${place.name}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={`group relative flex flex-col justify-between rounded-2xl border p-4 transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/40 ${
        isSelected
          ? "border-blue-500 bg-blue-50/70 shadow-md shadow-blue-500/10 ring-2 ring-blue-500/30 dark:border-blue-500 dark:bg-blue-950/40 dark:ring-blue-500/40"
          : "border-zinc-200/80 bg-white hover:border-blue-400 hover:shadow-md hover:shadow-blue-500/5 hover:-translate-y-0.5 dark:border-zinc-800/80 dark:bg-zinc-900/80 dark:hover:border-zinc-700 dark:hover:shadow-none"
      }`}
    >
      <div>
        {/* Header: Index Badge, Place Name & Selection Badge */}
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2 truncate">
            {typeof index === "number" && (
              <span
                className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg text-xs font-bold transition-colors ${
                  isSelected
                    ? "bg-blue-600 text-white shadow-xs"
                    : "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                }`}
              >
                {index}
              </span>
            )}

            <h3 className="text-sm sm:text-base font-bold tracking-tight text-zinc-900 dark:text-zinc-50 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate">
              {place.name}
            </h3>
          </div>

          {isSelected ? (
            <span className="inline-flex flex-shrink-0 items-center gap-1 rounded-full bg-blue-600 px-2.5 py-0.5 text-[10px] font-bold text-white shadow-xs animate-fade-in-up">
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
              </svg>
              Selected
            </span>
          ) : (
            <span
              className={`inline-flex flex-shrink-0 items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ring-1 ring-inset ${
                openStatus.variant === "open"
                  ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-950/50 dark:text-emerald-300 dark:ring-emerald-500/30"
                  : openStatus.variant === "closed"
                  ? "bg-rose-50 text-rose-700 ring-rose-600/20 dark:bg-rose-950/50 dark:text-rose-300 dark:ring-rose-500/30"
                  : "bg-zinc-100 text-zinc-600 ring-zinc-500/20 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  openStatus.variant === "open"
                    ? "bg-emerald-500"
                    : openStatus.variant === "closed"
                    ? "bg-rose-500"
                    : "bg-zinc-400"
                }`}
              />
              <span>{openStatus.text}</span>
            </span>
          )}
        </div>

        {/* Type & Price Level */}
        <div className="flex items-center gap-2 text-xs mb-2">
          <span className="font-semibold text-zinc-500 dark:text-zinc-400">
            {formattedType}
          </span>
          {priceSymbol && (
            <span className="rounded-md bg-emerald-50 px-1.5 py-0.5 text-[10px] font-extrabold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
              {priceSymbol}
            </span>
          )}
        </div>

        {/* Rating and Review Stats */}
        <div className="flex items-center gap-2 text-xs mb-2">
          <div className="flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 font-bold text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
            <svg
              className="h-3.5 w-3.5 fill-amber-400 text-amber-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10.868 2.884c-.321-.772-1.415-.772-1.736 0l-1.83 4.401-4.753.381c-.833.067-1.171 1.107-.536 1.651l3.62 3.102-1.106 4.637c-.194.813.691 1.456 1.405 1.02L10 15.591l4.064 2.485c.713.436 1.598-.207 1.404-1.02l-1.106-4.637 3.62-3.102c.635-.544.297-1.584-.536-1.65l-4.752-.382-1.831-4.401z"
                clipRule="evenodd"
              />
            </svg>
            <span>{formattedRating}</span>
          </div>
          <span className="text-zinc-500 dark:text-zinc-400 font-medium">
            ({formattedReviews})
          </span>
        </div>

        {/* Address */}
        {place.address ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400 line-clamp-2 leading-relaxed">
            📍 {place.address}
          </p>
        ) : (
          <p className="text-xs italic text-zinc-400 dark:text-zinc-500">
            Address not specified
          </p>
        )}
      </div>

      {/* Action Hierarchy */}
      <div className="mt-3.5 flex items-center justify-between gap-2 pt-3 border-t border-zinc-100 dark:border-zinc-800/80">
        {/* Primary in-app action */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(place.place_id);
          }}
          aria-label={`View ${place.name} on map`}
          className="inline-flex items-center gap-1 text-xs font-bold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/20 rounded-md px-1 py-0.5"
        >
          <span>View on map</span>
          <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>

        {/* External Actions: Secondary & Tertiary */}
        <div className="flex items-center gap-2">
          <a
            href={place.directions_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 px-2.5 py-1.5 text-xs font-semibold text-blue-700 shadow-2xs transition-all hover:from-blue-100 hover:to-indigo-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:from-blue-950/60 dark:to-indigo-950/60 dark:text-blue-300 dark:hover:from-blue-900/60 dark:hover:to-indigo-900/60"
            aria-label={`Get directions to ${place.name}`}
          >
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            Directions
          </a>

          <a
            href={place.google_maps_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-zinc-700 shadow-2xs transition-all hover:bg-zinc-50 hover:text-zinc-900 hover:border-zinc-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-zinc-800 dark:bg-zinc-800/80 dark:text-zinc-300 dark:hover:bg-zinc-700 dark:hover:text-zinc-100"
            aria-label={`View ${place.name} on Google Maps`}
          >
            <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Google Maps
          </a>
        </div>
      </div>
    </div>
  );
}
