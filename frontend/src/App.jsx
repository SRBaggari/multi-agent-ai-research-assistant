import { useEffect, useState } from "react";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";

import {
  getToken,
  getStoredUser,
  saveSession,
  clearSession,
  fetchCurrentUser,
  setUnauthorizedHandler,
} from "./services/api";

function App() {
  // The session is restored from localStorage so a page refresh does
  // not log the user out.
  const [token, setToken] = useState(getToken());
  const [user, setUser] = useState(getStoredUser());
  const [expiredNotice, setExpiredNotice] = useState("");

  const handleLogin = (newToken, newUser) => {
    saveSession(newToken, newUser);
    setExpiredNotice("");
    setToken(newToken);
    setUser(newUser);
  };

  const handleLogout = () => {
    clearSession();
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    // api.js calls this when any request comes back 401, which means
    // the stored token expired or is no longer valid.
    setUnauthorizedHandler(() => {
      setToken(null);
      setUser(null);
      setExpiredNotice("Your session has expired. Please sign in again.");
    });

    return () => setUnauthorizedHandler(null);
  }, []);

  useEffect(() => {
    // Check a restored token once on start-up. A 401 is handled by the
    // interceptor above; a network error is ignored so that a briefly
    // offline backend does not log the user out.
    if (!token) {
      return;
    }

    fetchCurrentUser()
      .then((currentUser) => setUser(currentUser))
      .catch(() => {});
    // Only re-run when the user signs in again.
  }, [token]);

  if (!token) {
    return <Login onLogin={handleLogin} notice={expiredNotice} />;
  }

  return <Dashboard user={user} onLogout={handleLogout} />;
}

export default App;
