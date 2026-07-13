const API_URL = "http://127.0.0.1:8001/chat";

export async function sendMessage(message) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to communicate with backend");
  }

  return await response.json();
}