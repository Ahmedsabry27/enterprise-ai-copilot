import { MessageSquare } from "lucide-react";

export default function ConversationItem({
  conversation,
  onClick,
  isActive,
}) {
  return (
    <button
      onClick={() => onClick?.(conversation)}
      className={`
        flex
        w-full
        items-center
        gap-2
        rounded-lg
        px-3
        py-2
        text-sm
        transition
        ${
          isActive
            ? "bg-accent font-medium"
            : "hover:bg-accent"
        }
      `}
    >
      <MessageSquare className="h-4 w-4 shrink-0" />

      <span className="truncate">
        {conversation.title}
      </span>
    </button>
  );
}