"use client";

import React, { KeyboardEvent, useEffect, useRef, useState } from "react";

interface ChatComposerProps {
  isSending: boolean;
  onSend: (text: string, coords?: { lat: number; lng: number }) => Promise<void>;
  placeholder?: string;
}

export function ChatComposer({
  isSending,
  onSend,
  placeholder = "Ask for restaurants, cafés, hotels, hospitals, ATMs, or places to visit…",
}: ChatComposerProps) {
  const [text, setText] = useState<string>("");
  const [isGettingLocation, setIsGettingLocation] = useState<boolean>(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isSending && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isSending]);

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        120
      )}px`;
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (isSending || !trimmed || trimmed.length < 2 || trimmed.length > 500) {
      return;
    }

    setText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    await onSend(trimmed);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleFormSubmit(e);
    }
  };

  const handleLocationClick = () => {
    if (!navigator.geolocation) return;
    const currentText = text.trim();
    setIsGettingLocation(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsGettingLocation(false);
        setText("");
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto";
        }
        onSend(currentText, {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
      },
      () => {
        setIsGettingLocation(false);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const isValidLength = text.trim().length >= 2 && text.trim().length <= 500;
  const isNearLimit = text.length > 400;

  return (
    <form
      onSubmit={handleFormSubmit}
      className="sticky bottom-0 z-20 border-t border-zinc-200/80 bg-white/90 p-3.5 backdrop-blur-xl dark:border-zinc-800/80 dark:bg-zinc-950/90"
    >
      <label htmlFor="chat-textarea" className="sr-only">
        Ask a local place prompt
      </label>

      <div className="relative flex flex-col gap-2 rounded-2xl border border-zinc-300/80 bg-white p-2.5 shadow-sm transition-all focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 dark:border-zinc-700/80 dark:bg-zinc-900/90 dark:focus-within:border-blue-400">
        <textarea
          id="chat-textarea"
          ref={textareaRef}
          rows={1}
          value={text}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          maxLength={500}
          disabled={isSending}
          placeholder={placeholder}
          className="max-h-28 min-h-[38px] w-full resize-none bg-transparent px-2.5 py-1 text-xs sm:text-sm font-medium text-zinc-900 placeholder-zinc-400 focus:outline-none disabled:bg-transparent disabled:text-zinc-400 dark:text-zinc-100 dark:placeholder-zinc-500"
        />

        {/* Toolbar & Action Buttons */}
        <div className="flex items-center justify-between gap-2 pt-1 border-t border-zinc-100 dark:border-zinc-800/60">
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handleLocationClick}
              disabled={isSending || isGettingLocation}
              title="Use current GPS location"
              className="inline-flex items-center gap-1 rounded-lg border border-zinc-200/80 bg-zinc-50 px-2 py-1 text-[11px] font-semibold text-zinc-600 hover:border-zinc-300 hover:bg-zinc-100 hover:text-zinc-900 transition-all focus:outline-none dark:border-zinc-800 dark:bg-zinc-800/60 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
            >
              {isGettingLocation ? (
                <svg className="h-3 w-3 animate-spin text-blue-600" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <span className="text-xs">📍</span>
              )}
              <span>Near Me</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            {isNearLimit && (
              <span className="text-[10px] font-mono text-zinc-400">
                {text.length}/500
              </span>
            )}

            <button
              type="submit"
              disabled={isSending || !isValidLength}
              aria-label="Send prompt to assistant"
              className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 text-white shadow-md shadow-blue-500/20 transition-all hover:opacity-95 hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:bg-zinc-300 disabled:opacity-40 dark:disabled:bg-zinc-800"
            >
              {isSending ? (
                <svg
                  className="h-4 w-4 animate-spin text-white"
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
              ) : (
                <svg
                  className="h-4 w-4 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M5 12h14M12 5l7 7-7 7"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
