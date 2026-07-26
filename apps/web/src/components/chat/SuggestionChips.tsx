"use client";

import React from "react";

const SUGGESTION_CATEGORIES = [
  {
    label: "Bakso di Gadog",
    query: "cariin gua tukang bakso di sekitar Gadog, Kabupaten Bogor",
    icon: "🍜",
  },
  {
    label: "Sundanese Food in Bogor",
    query: "Cari restoran Sunda di Bogor",
    icon: "🍲",
  },
  {
    label: "Quiet Coffee Shops near Sudirman",
    query: "Find quiet coffee shops near Sudirman Jakarta",
    icon: "☕",
  },
  {
    label: "Hotels in Sentul",
    query: "Find recommended hotels in Sentul Bogor",
    icon: "🏨",
  },
  {
    label: "Hospitals near Me",
    query: "Cari rumah sakit terdekat",
    icon: "🏥",
  },
];

interface SuggestionChipsProps {
  onSelectSuggestion: (query: string) => void;
  disabled?: boolean;
}

export function SuggestionChips({
  onSelectSuggestion,
  disabled,
}: SuggestionChipsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 pt-1">
      {SUGGESTIONS.map((item) => (
        <button
          key={item.label}
          type="button"
          disabled={disabled}
          onClick={() => onSelectSuggestion(item.query)}
          className="group inline-flex items-center gap-1.5 rounded-full border border-zinc-200/90 bg-white/90 px-3 py-1.5 text-xs font-semibold text-zinc-700 shadow-2xs transition-all hover:border-blue-500/80 hover:bg-blue-50/60 hover:text-blue-700 hover:shadow-xs hover:scale-[1.02] active:scale-98 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-900/90 dark:text-zinc-300 dark:hover:border-blue-500/80 dark:hover:bg-blue-950/50 dark:hover:text-blue-300"
        >
          <span className="text-sm transition-transform group-hover:scale-110">
            {item.icon}
          </span>
          <span>{item.label}</span>
        </button>
      ))}
    </div>
  );
}

const SUGGESTIONS = SUGGESTION_CATEGORIES;
