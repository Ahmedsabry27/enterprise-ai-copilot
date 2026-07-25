import api from "./api";

export async function sendMessage(message, conversationId = null) {
  const { data } = await api.post("/chat", {
    message,
    conversation_id: conversationId,
  });

  return data;
}