import { useEffect, useRef } from "react";

import Message from "./Message";
import TypingIndicator from "./TypingIndicator";

export default function MessageList({
  messages = [],
  loading = false,
}) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      {messages.length === 0 ? (
        <div className="flex flex-1 items-center justify-center px-8">
          <div className="max-w-2xl text-center">

            <h1 className="mb-4 text-4xl font-bold tracking-tight">
              Enterprise AI
            </h1>

            <p className="mb-10 text-lg text-muted-foreground">
              How can I help you today?
            </p>

            <div className="grid gap-4 sm:grid-cols-2">

              <div className="rounded-2xl border bg-card p-5 text-left transition hover:shadow-md">
                <h3 className="mb-2 font-semibold">
                  📄 Summarize Documents
                </h3>
                <p className="text-sm text-muted-foreground">
                  Upload files and receive concise summaries and key insights.
                </p>
              </div>

              <div className="rounded-2xl border bg-card p-5 text-left transition hover:shadow-md">
                <h3 className="mb-2 font-semibold">
                  💻 Generate Code
                </h3>
                <p className="text-sm text-muted-foreground">
                  Create, explain, and improve code in multiple languages.
                </p>
              </div>

              <div className="rounded-2xl border bg-card p-5 text-left transition hover:shadow-md">
                <h3 className="mb-2 font-semibold">
                  📊 Analyze Data
                </h3>
                <p className="text-sm text-muted-foreground">
                  Understand trends, metrics, reports, and dashboards.
                </p>
              </div>

              <div className="rounded-2xl border bg-card p-5 text-left transition hover:shadow-md">
                <h3 className="mb-2 font-semibold">
                  ✨ Generate Content
                </h3>
                <p className="text-sm text-muted-foreground">
                  Draft emails, user stories, PRDs, presentations, and more.
                </p>
              </div>

            </div>
          </div>
        </div>
      ) : (
        <div className="mx-auto flex w-full max-w-6xl flex-col px-6 py-8">

          {messages.map((message) => (
            <Message
              key={message.id}
              message={message}
            />
          ))}

          {loading && <TypingIndicator />}

          <div ref={messagesEndRef} />

        </div>
      )}
    </div>
  );
}