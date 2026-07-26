"use client";

import React from "react";
import { Place } from "@/types/place";
import { formatOpenStatus, formatPrimaryType, formatRating } from "@/lib/formatters";

interface SelectedPlaceOverlayProps {
  place: Place;
  onClose: () => void;
}

export function SelectedPlaceOverlay({
  place,
  onClose,
}: SelectedPlaceOverlayProps) {
  const openStatus = formatOpenStatus(place.open_now);
  const formattedType = formatPrimaryType(place.primary_type);
  const formattedRating = formatRating(place.rating);

  return (
    <div className="absolute top-4 left-4 right-4 sm:left-auto sm:right-4 sm:w-80 z-20 rounded-2xl border border-zinc-200 bg-white/95 p-4 shadow-xl backdrop-blur-md dark:border-zinc-800 dark:bg-zinc-900/95 transition-all">
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div>
          <span className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
            {formattedType}
          </span>
          <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 line-clamp-1">
            {place.name}
          </h3>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close place summary"
          className="rounded-lg p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {place.address && (
        <p className="text-xs text-zinc-500 dark:text-zinc-400 line-clamp-1 mb-2">
          {place.address}
        </p>
      )}

      <div className="flex items-center justify-between text-xs mb-3">
        <div className="flex items-center gap-1 font-semibold text-amber-600 dark:text-amber-400">
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

        <span
          className={`rounded-md px-2 py-0.5 text-[10px] font-medium ${
            openStatus.variant === "open"
              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
              : openStatus.variant === "closed"
              ? "bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300"
              : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
          }`}
        >
          {openStatus.text}
        </span>
      </div>

      <div className="flex items-center gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
        <a
          href={place.google_maps_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 flex items-center justify-center gap-1 rounded-lg border border-zinc-200 bg-white py-1.5 text-xs font-semibold text-zinc-700 shadow-2xs hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
        >
          Maps
        </a>
        <a
          href={place.directions_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-blue-600 py-1.5 text-xs font-semibold text-white shadow-2xs hover:bg-blue-700"
        >
          Directions
        </a>
      </div>
    </div>
  );
}
