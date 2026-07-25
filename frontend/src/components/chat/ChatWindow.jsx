import EmptyState from "./EmptyState";
import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";

export default function ChatWindow({ messages = [], loading = false }) {
  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        <EmptyState />
      ) : (
        <MessageList messages={messages} />
      )}

      {loading && <TypingIndicator />}
    </div>
  );
}