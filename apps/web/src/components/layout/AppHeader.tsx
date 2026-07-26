"use client";

import React from "react";

interface AppHeaderProps {
  onClearChat?: () => void;
  hasMessages?: boolean;
  isSending?: boolean;
}

export function AppHeader({
  onClearChat,
  hasMessages,
  isSending,
}: AppHeaderProps) {
  const handleNewChatClick = () => {
    if (!onClearChat) return;
    if (hasMessages) {
      const confirmed = window.confirm(
        "Start a new chat? Current conversation will be cleared."
      );
      if (!confirmed) return;
    }
    onClearChat();
  };

  return (
    <header className="sticky top-0 z-30 w-full border-b border-zinc-200/80 bg-white/80 px-4 py-3 backdrop-blur-xl dark:border-zinc-800/80 dark:bg-zinc-950/80 sm:px-6">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        {/* Brand & Logo */}
        <div className="flex items-center gap-3">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-500 font-bold text-white text-base shadow-md shadow-blue-500/25 ring-1 ring-white/20">
            P
            <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500 dark:border-zinc-950" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-lg">
                Pico Maps AI
              </h1>
              <span className="hidden sm:inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700 ring-1 ring-blue-600/20 ring-inset dark:bg-blue-950/60 dark:text-blue-300 dark:ring-blue-500/30">
                qwen3:4b
              </span>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 hidden sm:block">
              Local AI place assistant
            </p>
          </div>
        </div>

        {/* Right Status & Actions */}
        <div className="flex items-center gap-2 text-xs">
          <div className="hidden md:flex items-center gap-2 rounded-full border border-zinc-200/80 bg-zinc-50/80 px-3 py-1 font-medium text-zinc-600 dark:border-zinc-800/80 dark:bg-zinc-900/80 dark:text-zinc-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span>Google Places</span>
          </div>

          {onClearChat && (
            <button
              type="button"
              onClick={handleNewChatClick}
              disabled={isSending}
              aria-label="Start a new chat"
              title="Start a new chat and reset conversation context"
              className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-200/80 bg-white px-2.5 py-1.5 font-semibold text-zinc-700 shadow-2xs transition-all hover:bg-zinc-100 hover:text-zinc-900 focus:outline-none focus:ring-2 focus:ring-blue-500/20 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
            >
              <svg
                className="h-3.5 w-3.5 text-zinc-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 4v16m8-8H4"
                />
              </svg>
              <span>New Chat</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
