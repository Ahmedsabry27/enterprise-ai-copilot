import MessageBubble from "./MessageBubble";

function MessageList({ messages }) {
  return (
    <>
      {messages.map((message, index) => (
        <MessageBubble
          key={index}
          role={message.role}
          text={message.text}
        />
      ))}
    </>
  );
}

export default MessageList;