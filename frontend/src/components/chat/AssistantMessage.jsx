import Avatar from "./Avatar";
import CopyButton from "./CopyButton";
import MarkdownRenderer from "./MarkdownRenderer";

export default function AssistantMessage({ message }) {
  return (
    <div className="group mb-10 flex animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="flex w-full max-w-5xl gap-5">

        {/* Avatar */}

        <Avatar />

        {/* Message */}

        <div className="relative flex-1">

          {/* Copy Button */}

          <div className="absolute right-0 top-0 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
            <CopyButton text={message.content} />
          </div>

          {/* AI Response */}

          <div className="rounded-3xl bg-card px-8 py-6 shadow-sm ring-1 ring-border/50">

            <MarkdownRenderer>
              {message.content}
            </MarkdownRenderer>

          </div>

        </div>

      </div>
    </div>
  );
}