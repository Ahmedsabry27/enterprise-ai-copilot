import { Bot, Sparkles } from "lucide-react";

const suggestions = [
  "Design an AWS architecture",
  "Explain Amazon Bedrock",
  "Generate a SQL query",
  "Review my code",
];

export default function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-600">
        <Bot className="h-8 w-8 text-white" />
      </div>

      <h1 className="text-3xl font-bold">Enterprise AI</h1>

      <p className="mt-2 text-muted-foreground">
        How can I help you today?
      </p>

      <div className="mt-10 grid w-full max-w-3xl grid-cols-1 gap-4 md:grid-cols-2">
        {suggestions.map((item) => (
          <button
            key={item}
            className="rounded-xl border bg-card p-5 text-left transition hover:bg-accent"
          >
            <div className="mb-2 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-emerald-500" />
              <span className="font-medium">{item}</span>
            </div>

            <p className="text-sm text-muted-foreground">
              Click to start a conversation.
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}