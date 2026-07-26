"use client";

import React, { Suspense } from "react";
import { useChat } from "@/hooks/useChat";
import { MainLayout } from "@/components/layout/MainLayout";
import { TypingIndicator } from "@/components/chat/TypingIndicator";

function ConversationalMapApp() {
  const chatState = useChat();
  return <MainLayout chatState={chatState} />;
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center bg-white dark:bg-zinc-950 p-6">
          <TypingIndicator />
        </div>
      }
    >
      <ConversationalMapApp />
    </Suspense>
  );
}
