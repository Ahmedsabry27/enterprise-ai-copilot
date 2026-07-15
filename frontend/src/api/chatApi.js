const API_URL = `${import.meta.env.VITE_API_URL}/chat`;

console.log("API URL:", API_URL);

export async function sendMessage(message) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error("Failed to communicate with backend");
  }

  return response.json();
}