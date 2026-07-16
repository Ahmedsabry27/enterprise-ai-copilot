export default function createConversationTitle(
  message
) {
  const title = message
    .trim()
    .replace(/\s+/g, " ");

  if (title.length <= 50) {
    return title;
  }

  return title.substring(0, 50) + "...";
}