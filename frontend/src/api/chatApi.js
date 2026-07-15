const API_URL = `${import.meta.env.VITE_API_URL}/chat`;

console.log("API URL:", API_URL);

export async function sendMessage(message, previousResponseId = null) {
  const payload = {
    message: message,
    previous_response_id: previousResponseId,
  };

  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Failed to communicate with backend");
  }

  return response.json();
}