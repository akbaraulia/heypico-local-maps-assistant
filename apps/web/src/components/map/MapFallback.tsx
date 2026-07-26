import React from "react";

interface MapFallbackProps {
  message?: string;
}

export function MapFallback({ message }: MapFallbackProps) {
  return (
    <div className="flex h-full min-h-[300px] w-full flex-col items-center justify-center rounded-2xl border border-dashed border-zinc-300 bg-zinc-100/60 p-6 text-center dark:border-zinc-800 dark:bg-zinc-900/50">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400 mb-3">
        <svg
          className="h-6 w-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
          />
        </svg>
      </div>

      <h3 className="text-sm font-bold text-zinc-800 dark:text-zinc-200">
        Interactive Map Unavailable
      </h3>
      <p className="mt-1.5 text-xs text-zinc-600 dark:text-zinc-400 max-w-sm leading-relaxed">
        {message || "Add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY to display the interactive map."}
      </p>

      <div className="mt-4 rounded-lg bg-zinc-200/70 px-3 py-1.5 font-mono text-[11px] text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
        NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=YOUR_KEY
      </div>
    </div>
  );
}
