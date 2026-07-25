import api from "./api";

/**
 * Create a new conversation
 */
export async function createConversation(title = "New Conversation") {
  try {
    const { data } = await api.post("/conversations", {
      title,
    });

    return data;
  } catch (error) {
    console.error("Failed to create conversation:", error);
    throw error;
  }
}

/**
 * Get all conversations
 */
export async function getConversations() {
  try {
    const { data } = await api.get("/conversations");
    return data;
  } catch (error) {
    console.error("Failed to load conversations:", error);
    throw error;
  }
}

/**
 * Get all messages for a conversation
 */
export async function getConversationMessages(conversationId) {
  try {
    const { data } = await api.get(
      `/conversations/${conversationId}/messages`
    );

    return data;
  } catch (error) {
    console.error(
      `Failed to load messages for conversation ${conversationId}:`,
      error
    );
    throw error;
  }
}

/**
 * Rename a conversation
 */
export async function renameConversation(conversationId, title) {
  try {
    const { data } = await api.patch(
      `/conversations/${conversationId}`,
      {
        title,
      }
    );

    return data;
  } catch (error) {
    console.error(
      `Failed to rename conversation ${conversationId}:`,
      error
    );
    throw error;
  }
}

/**
 * Delete a conversation
 */
export async function deleteConversation(conversationId) {
  try {
    await api.delete(`/conversations/${conversationId}`);
  } catch (error) {
    console.error(
      `Failed to delete conversation ${conversationId}:`,
      error
    );
    throw error;
  }
}