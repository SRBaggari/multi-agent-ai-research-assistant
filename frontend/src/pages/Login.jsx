import { useState } from "react";

import { login, register, getErrorMessage } from "../services/api";

function Login({ onLogin, notice }) {
  const [isRegister, setIsRegister] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError("Email and password are required.");
      return;
    }

    if (isRegister && !name.trim()) {
      setError("Please enter your name.");
      return;
    }

    if (isRegister && password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    try {
      setLoading(true);

      const data = isRegister
        ? await register(name.trim(), email.trim(), password)
        : await login(email.trim(), password);

      onLogin(data.token, data.user);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <h1>AI Research Assistant</h1>

        <p className="muted">
          {isRegister
            ? "Create an account to get started."
            : "Sign in to analyse your research papers."}
        </p>

        {isRegister && (
          <label>
            Name
            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Your name"
              autoComplete="name"
            />
          </label>
        )}

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="At least 6 characters"
            autoComplete={isRegister ? "new-password" : "current-password"}
          />
        </label>

        {notice && !error && <div className="notice">{notice}</div>}

        {error && (
          <div className="error" role="alert" data-testid="auth-error">
            {error}
          </div>
        )}

        <button type="submit" disabled={loading}>
          {loading
            ? "Please wait..."
            : isRegister
            ? "Create account"
            : "Sign in"}
        </button>

        <button
          type="button"
          className="link-button"
          onClick={() => {
            setIsRegister(!isRegister);
            setError("");
          }}
        >
          {isRegister
            ? "Already have an account? Sign in"
            : "New here? Create an account"}
        </button>
      </form>
    </div>
  );
}

export default Login;
