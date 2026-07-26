"use client";

import React from "react";
import { SuggestionChips } from "./SuggestionChips";

interface WelcomeMessageProps {
  content?: string;
  onSelectSuggestion: (query: string) => void;
  disabled?: boolean;
}

export function WelcomeMessage({
  onSelectSuggestion,
  disabled,
}: WelcomeMessageProps) {
  return (
    <div className="animate-fade-in-up flex flex-col gap-4 rounded-3xl border border-zinc-200/80 bg-gradient-to-b from-white to-zinc-50/50 p-5 shadow-xs dark:border-zinc-800/80 dark:from-zinc-900/90 dark:to-zinc-950/60">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 font-bold text-white text-xs shadow-md shadow-blue-500/20">
          ✨
        </div>
        <div>
          <h2 className="text-sm font-bold text-zinc-900 dark:text-zinc-50">
            Pico Maps Assistant
          </h2>
          <p className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
            Local AI with verified Google Places
          </p>
        </div>
      </div>

      <p className="text-xs sm:text-sm leading-relaxed font-medium text-zinc-700 dark:text-zinc-300">
        Ask for places to eat, visit, shop, stay, or explore.
      </p>

      <div className="pt-2 border-t border-zinc-100 dark:border-zinc-800/80">
        <span className="block text-[11px] font-bold uppercase tracking-wider text-zinc-400 dark:text-zinc-500 mb-2">
          Suggested Prompts:
        </span>
        <SuggestionChips
          onSelectSuggestion={onSelectSuggestion}
          disabled={disabled}
        />
      </div>
    </div>
  );
}
