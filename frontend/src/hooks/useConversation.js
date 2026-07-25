import { useEffect, useState, useCallback } from "react";
import { getConversations } from "../services/conversationService";

export default function useConversations() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  const refreshConversations = useCallback(async () => {
    setLoading(true);

    try {
      const data = await getConversations();

      // Always keep conversations as an array
      setConversations(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to load conversations:", error);

      // Prevent undefined state after an error
      setConversations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  return {
    conversations,
    loading,
    refreshConversations,
  };
}