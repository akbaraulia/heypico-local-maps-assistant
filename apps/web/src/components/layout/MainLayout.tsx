"use client";

import React from "react";
import { UseChatReturn } from "@/hooks/useChat";
import { ChatPanel } from "../chat/ChatPanel";
import { ChatComposer } from "../chat/ChatComposer";
import { PlacesMap } from "../map/PlacesMap";

interface MainLayoutProps {
  chatState: UseChatReturn;
}

export function MainLayout({ chatState }: MainLayoutProps) {
  const { isMapExpanded, closeMap, isSending, sendMessage } = chatState;

  if (isMapExpanded) {
    return (
      <div className="flex flex-1 flex-col lg:flex-row overflow-hidden h-screen w-full bg-white dark:bg-zinc-950 font-sans antialiased text-zinc-900 dark:text-zinc-50">
        {/* Left Chat Panel (42% width on desktop) */}
        <div className="w-full lg:w-[42%] border-b lg:border-b-0 lg:border-r border-zinc-200/80 dark:border-zinc-800/80 flex flex-col min-h-0 h-full">
          <div className="flex-1 overflow-hidden flex flex-col min-h-0">
            <ChatPanel chatState={chatState} />
          </div>
          <ChatComposer
            isSending={isSending}
            onSend={(text, coords) => sendMessage(text, coords)}
          />
        </div>

        {/* Right Expanded Map Panel (58% width on desktop / Full view on mobile) */}
        <div className="w-full h-[50vh] lg:h-full lg:w-[58%] p-3 sm:p-4 lg:p-6 bg-zinc-50/70 dark:bg-zinc-900/50 flex flex-col relative">
          {/* Top Bar for Map Controls */}
          <div className="flex items-center justify-between pb-3">
            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-blue-600 animate-pulse" />
                <h2 className="text-xs sm:text-sm font-bold text-zinc-900 dark:text-zinc-100">
                  Interactive Multi-Place Map View
                </h2>
              </div>
              <span className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                • Select a marker to view place details.
              </span>
            </div>

            <button
              type="button"
              onClick={closeMap}
              aria-label="Close expanded map"
              className="inline-flex items-center gap-1.5 rounded-xl bg-zinc-200/80 px-3 py-1.5 text-xs font-semibold text-zinc-800 hover:bg-zinc-300 transition-all active:scale-95 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
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
              Close map
            </button>
          </div>

          <div className="flex-1 relative overflow-hidden rounded-2xl border border-zinc-200/80 shadow-xs dark:border-zinc-800/80">
            <PlacesMap
              places={chatState.activePlaces}
              selectedPlaceId={chatState.selectedPlaceId}
              onSelectPlace={chatState.selectPlace}
            />
          </div>
        </div>
      </div>
    );
  }

  // Default UX: Centered Chatbot Experience (No permanent right-side map)
  return (
    <div className="flex flex-col h-screen w-full bg-white dark:bg-zinc-950 font-sans antialiased text-zinc-900 dark:text-zinc-50 overflow-hidden">
      <div className="mx-auto flex h-full w-full max-w-3xl sm:max-w-4xl flex-col min-h-0 shadow-2xl shadow-zinc-200/30 dark:shadow-none">
        <div className="flex-1 overflow-hidden flex flex-col min-h-0">
          <ChatPanel chatState={chatState} />
        </div>
        <ChatComposer
          isSending={isSending}
          onSend={(text, coords) => sendMessage(text, coords)}
        />
      </div>
    </div>
  );
}
