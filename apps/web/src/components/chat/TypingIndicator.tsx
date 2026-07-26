import React from "react";

export function TypingIndicator() {
  return (
    <div
      aria-live="polite"
      aria-busy="true"
      className="animate-fade-in-up flex w-full items-start gap-3"
    >
      <div className="relative flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 font-bold text-white text-xs shadow-md shadow-blue-500/20 ring-2 ring-white dark:ring-zinc-950">
        AI
      </div>

      <div className="flex flex-col gap-1.5 max-w-sm">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-zinc-900 dark:text-zinc-100">
            Pico
          </span>
        </div>

        <div className="flex items-center gap-2.5 rounded-2xl rounded-tl-xs border border-zinc-200/80 bg-white px-4 py-3 text-xs font-medium text-zinc-600 shadow-xs dark:border-zinc-800/80 dark:bg-zinc-900 dark:text-zinc-400">
          <span className="flex gap-1 items-center">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse-glow" />
            <span className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse-glow [animation-delay:0.3s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-blue-600 animate-pulse-glow [animation-delay:0.6s]" />
          </span>
          <span>Thinking and checking verified places…</span>
        </div>
      </div>
    </div>
  );
}
