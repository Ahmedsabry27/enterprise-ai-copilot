import axios from "axios";
import { getAccessToken } from "./auth";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// --------------------------------------------------
// Request Interceptor
// --------------------------------------------------
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await getAccessToken();

      console.group("🚀 API Request");
      console.log("URL:", `${config.baseURL}${config.url}`);
      console.log("Method:", config.method?.toUpperCase());

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;

        console.log("✅ Access Token Found");
        console.log("Token Preview:", `${token.substring(0, 30)}...`);
      } else {
        console.warn("⚠️ No access token found.");
      }

      console.log("Headers:", config.headers);
      console.groupEnd();

      return config;
    } catch (error) {
      console.error("❌ Failed to retrieve access token:", error);
      return Promise.reject(error);
    }
  },
  (error) => Promise.reject(error)
);

// --------------------------------------------------
// Response Interceptor
// --------------------------------------------------
api.interceptors.response.use(
  (response) => {
    console.group("✅ API Response");
    console.log("Status:", response.status);
    console.log("URL:", response.config.url);
    console.log("Data:", response.data);
    console.groupEnd();

    return response;
  },
  (error) => {
    console.group("❌ API Error");

    if (error.response) {
      console.log("Status:", error.response.status);
      console.log("Data:", error.response.data);
      console.log("Headers:", error.response.headers);
    } else {
      console.log("Message:", error.message);
    }

    console.groupEnd();

    return Promise.reject(error);
  }
);

export default api;