const API_URL = `${import.meta.env.VITE_API_URL}/conversations`;

// --------------------------------------------------
// Create Conversation
// --------------------------------------------------
export async function createConversation(
  title = "New Conversation"
) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to create conversation");
  }

  return response.json();
}

// --------------------------------------------------
// Get All Conversations
// --------------------------------------------------
export async function getConversations() {
  const response = await fetch(API_URL);

  if (!response.ok) {
    throw new Error("Failed to load conversations");
  }

  return response.json();
}

// --------------------------------------------------
// Get Single Conversation
// --------------------------------------------------
export async function getConversation(id) {
  const response = await fetch(`${API_URL}/${id}`);

  if (!response.ok) {
    throw new Error("Conversation not found");
  }

  return response.json();
}

// --------------------------------------------------
// Get Messages for a Conversation
// --------------------------------------------------
export async function getMessages(
  conversationId
) {
  const response = await fetch(
    `${API_URL}/${conversationId}/messages`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to load messages"
    );
  }

  return response.json();
}

// --------------------------------------------------
// Delete Conversation
// --------------------------------------------------
export async function deleteConversation(id) {
  const response = await fetch(`${API_URL}/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error("Delete failed");
  }

  return true;
}

// --------------------------------------------------
// Update Conversation Title
// --------------------------------------------------
export async function updateConversationTitle(
  id,
  title
) {
  const response = await fetch(
    `${API_URL}/${id}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      "Failed to update conversation title"
    );
  }

  return response.json();
}