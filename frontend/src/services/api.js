import axios from "axios";

// The backend URL comes from frontend/.env so it can change per machine.
const BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

const API = axios.create({
  baseURL: BASE_URL,
});

const TOKEN_KEY = "research_token";
const USER_KEY = "research_user";

// --------------------------------------------------
// Token storage
// --------------------------------------------------

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const getStoredUser = () => {
  const raw = localStorage.getItem(USER_KEY);
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const saveSession = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token);
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
};

export const clearSession = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

// Attach the JWT to every request when the user is logged in.
API.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --------------------------------------------------
// Expired / rejected tokens
// --------------------------------------------------

// App.jsx registers a callback here so that a 401 on a normal request
// sends the user back to the login screen instead of leaving the
// dashboard in a broken state.
let unauthorizedHandler = null;

export const setUnauthorizedHandler = (handler) => {
  unauthorizedHandler = handler;
};

API.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const url = error?.config?.url || "";

    // A failed login attempt also returns 401 - that is not an expired
    // session, so it must not trigger a logout.
    const isLoginAttempt =
      url.includes("/auth/login") || url.includes("/auth/register");

    if (status === 401 && !isLoginAttempt && getToken()) {
      clearSession();
      if (unauthorizedHandler) {
        unauthorizedHandler();
      }
    }

    return Promise.reject(error);
  }
);

// --------------------------------------------------
// Error handling
// --------------------------------------------------

/**
 * Turn an axios error into a readable message.
 * FastAPI sends { "detail": "..." } for handled errors and a list of
 * field errors for validation failures.
 */
export const getErrorMessage = (error) => {
  // No response at all = the backend is down or CORS blocked the call.
  if (!error?.response) {
    return (
      "Could not reach the server. " +
      `Make sure the backend is running at ${BASE_URL}.`
    );
  }

  const status = error.response.status;
  const detail = error.response.data?.detail;

  // 422 = FastAPI validation error, which arrives as a list of fields.
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc)
          ? item.loc[item.loc.length - 1]
          : "";
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .join(", ");
  }

  if (typeof detail === "string" && detail.trim()) {
    // 502 means the OpenAI call failed; the backend already explains why.
    return status === 502 ? `AI service error: ${detail}` : detail;
  }

  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }

  return `Request failed with status ${status}.`;
};

// --------------------------------------------------
// Authentication
// --------------------------------------------------

export const register = async (name, email, password) => {
  const response = await API.post("/auth/register", {
    name,
    email,
    password,
  });
  return response.data;
};

export const login = async (email, password) => {
  const response = await API.post("/auth/login", { email, password });
  return response.data;
};

/** Confirm a stored token is still valid. Does not touch MongoDB. */
export const fetchCurrentUser = async () => {
  const response = await API.get("/auth/me");
  return response.data;
};

// --------------------------------------------------
// Health
// --------------------------------------------------

/**
 * GET /health - reports whether MongoDB is reachable, whether an
 * OpenAI key is configured, and how many chunks are indexed.
 */
export const checkHealth = async () => {
  const response = await API.get("/health");
  return response.data;
};

// --------------------------------------------------
// Papers
// --------------------------------------------------

export const uploadPaper = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await API.post("/papers/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
};

export const listPapers = async () => {
  const response = await API.get("/papers");
  return response.data;
};

export const deletePaper = async (paperId) => {
  const response = await API.delete(`/papers/${paperId}`);
  return response.data;
};

// --------------------------------------------------
// Research
// --------------------------------------------------

export const askQuestion = async (query, topK = 6) => {
  const response = await API.post("/research/ask", {
    query,
    top_k: topK,
  });
  return response.data;
};

export default API;
