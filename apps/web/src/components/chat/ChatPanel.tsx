"use client";

import React, { useEffect, useRef, useState } from "react";
import { UseChatReturn } from "@/hooks/useChat";
import { AppHeader } from "../layout/AppHeader";
import { ChatMessage } from "./ChatMessage";
import { WelcomeMessage } from "./WelcomeMessage";
import { TypingIndicator } from "./TypingIndicator";

interface ChatPanelProps {
  chatState: UseChatReturn;
}

export function ChatPanel({ chatState }: ChatPanelProps) {
  const {
    messages,
    isSending,
    selectedPlaceId,
    activeMessageIdWithPlaces,
    sendMessage,
    retryMessage,
    selectPlace,
    selectMessagePlaces,
    expandMap,
    clearChatHistory,
  } = chatState;

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollBottom, setShowScrollBottom] = useState<boolean>(false);

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  // Auto-scroll to bottom on new messages or typing indicator
  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isFarFromBottom = scrollHeight - scrollTop - clientHeight > 150;
    setShowScrollBottom(isFarFromBottom);
  };

  const handleSuggestionSelect = (query: string) => {
    sendMessage(query);
  };

  const handleLocationSelected = (coords: { lat: number; lng: number }) => {
    sendMessage("Using my current location", coords);
  };

  const hasUserMessages = messages.some((m) => m.role === "user");

  return (
    <div className="relative flex flex-col h-full bg-zinc-50/40 dark:bg-zinc-950/40 min-h-0 overflow-hidden ambient-glow">
      <AppHeader
        onClearChat={clearChatHistory}
        hasMessages={hasUserMessages}
        isSending={isSending}
      />

      {/* Scrollable Conversation Container */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col gap-4 max-w-3xl w-full mx-auto"
      >
        {messages.map((msg, index) => {
          if (index === 0 && msg.id === "msg-welcome-01") {
            return (
              <WelcomeMessage
                key={msg.id}
                onSelectSuggestion={handleSuggestionSelect}
                disabled={isSending}
              />
            );
          }

          if (msg.status === "sending" && !msg.content) {
            return null;
          }

          return (
            <ChatMessage
              key={msg.id}
              message={msg}
              selectedPlaceId={selectedPlaceId}
              activeMessageIdWithPlaces={activeMessageIdWithPlaces}
              onSelectPlace={selectPlace}
              onSelectMessagePlaces={selectMessagePlaces}
              onLocationSelected={handleLocationSelected}
              onExpandMap={(msgId) => expandMap(msgId)}
              onRetry={retryMessage}
            />
          );
        })}

        {isSending && <TypingIndicator />}
      </div>

      {/* Jump to latest button */}
      {showScrollBottom && (
        <button
          type="button"
          onClick={scrollToBottom}
          aria-label="Scroll to latest messages"
          className="absolute bottom-4 right-6 z-20 inline-flex items-center gap-1.5 rounded-full border border-zinc-200/80 bg-white/90 px-3 py-1.5 text-xs font-bold text-zinc-700 shadow-md backdrop-blur-md hover:bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-900/90 dark:text-zinc-300 dark:hover:bg-zinc-800 animate-fade-in-up"
        >
          <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
          <span>Jump to latest</span>
        </button>
      )}
    </div>
  );
}
