"use client";

import React from "react";
import { useBrowserLocation } from "@/hooks/useBrowserLocation";

interface LocationClarificationProps {
  onLocationSelected: (coords: { lat: number; lng: number }) => void;
  disabled?: boolean;
}

export function LocationClarification({
  onLocationSelected,
  disabled,
}: LocationClarificationProps) {
  const { isLoading, error, requestLocation } = useBrowserLocation();

  const handleUseCurrentLocation = async () => {
    try {
      const coords = await requestLocation();
      onLocationSelected(coords);
    } catch {
      // Error state handled inside hook
    }
  };

  return (
    <div className="mt-3 flex flex-col gap-2 rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-xs dark:border-amber-900/40 dark:bg-amber-950/30">
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold text-amber-900 dark:text-amber-200">
          Location Required
        </span>
      </div>

      <p className="text-amber-800 dark:text-amber-300 text-[11px]">
        You can use your current location or type a city, district, or landmark below.
      </p>

      <div className="flex flex-wrap items-center gap-2 pt-1">
        <button
          type="button"
          disabled={isLoading || disabled}
          onClick={handleUseCurrentLocation}
          className="inline-flex items-center gap-1.5 rounded-lg bg-amber-600 px-3 py-1.5 font-semibold text-white shadow-xs transition-colors hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500/20 disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <svg
                className="h-3.5 w-3.5 animate-spin text-white"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Acquiring location...
            </>
          ) : (
            <>
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
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              Use my current location
            </>
          )}
        </button>
      </div>

      {error && (
        <p role="alert" className="mt-1 text-[11px] font-medium text-rose-600 dark:text-rose-400">
          {error}
        </p>
      )}
    </div>
  );
}
