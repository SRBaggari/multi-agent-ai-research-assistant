import { useState } from "react";

import { askQuestion, getErrorMessage } from "../services/api";

// Shown under the input so the user knows which agents exist.
const EXAMPLES = [
  "What is the main contribution of this paper?",
  "Compare the methodology of these papers.",
  "What are the research gaps?",
  "Give me a literature review.",
  "Summarize this paper.",
];

const AGENT_LABELS = {
  qa: "Q&A Agent",
  comparison: "Comparison Agent",
  gap: "Research Gap Agent",
  literature: "Literature Review Agent",
  summarizer: "Summarizer Agent",
};

function ChatBox({ indexedChunks }) {
  const [question, setQuestion] = useState("");
  const [topK, setTopK] = useState(6);

  const [answer, setAnswer] = useState("");
  const [agent, setAgent] = useState("");
  const [sources, setSources] = useState([]);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    setError("");

    if (!question.trim()) {
      setError("Please type a question first.");
      return;
    }

    try {
      setLoading(true);
      setAnswer("");
      setAgent("");
      setSources([]);

      const result = await askQuestion(question.trim(), topK);

      setAnswer(result.answer);
      setAgent(result.agent);
      setSources(result.sources || []);
    } catch (requestError) {
      // Show the real reason from the backend, not a generic message.
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Ask a research question</h2>

      {indexedChunks === 0 && (
        <p className="muted" data-testid="no-papers-hint">
          Upload at least one PDF before asking a question.
        </p>
      )}

      <textarea
        value={question}
        rows={4}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="Ask something about your research papers..."
        data-testid="question-input"
      />

      <div className="controls">
        <label className="inline">
          Sources to use
          <input
            type="number"
            min="1"
            max="20"
            value={topK}
            onChange={(event) => setTopK(Number(event.target.value))}
          />
        </label>

        <button onClick={ask} disabled={loading} data-testid="ask-button">
          {loading ? "Analysing..." : "Ask assistant"}
        </button>
      </div>

      <div className="examples">
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            className="chip"
            onClick={() => setQuestion(example)}
          >
            {example}
          </button>
        ))}
      </div>

      {loading && (
        <p className="muted" data-testid="loading-state">
          Retrieving relevant chunks and routing to an agent...
        </p>
      )}

      {error && (
        <div className="error" role="alert" data-testid="ask-error">
          {error}
        </div>
      )}

      {agent && (
        <div className="agent" data-testid="agent-used">
          <strong>Agent used:</strong> {AGENT_LABELS[agent] || agent}
        </div>
      )}

      {answer && (
        <div className="answer" data-testid="answer">
          <h3>Answer</h3>
          {/* Preserves the line breaks and headings the agents produce. */}
          <pre className="answer-text">{answer}</pre>
        </div>
      )}

      {sources.length > 0 && (
        <div className="sources" data-testid="sources">
          <h3>Sources ({sources.length})</h3>

          {sources.map((source, index) => (
            <details
              className="source"
              key={`${source.paper_id}-${index}`}
              data-testid="source-item"
            >
              <summary>
                <strong>{source.filename}</strong>
                <span className="muted"> Page {source.page_number}</span>
              </summary>
              <p className="source-text">{source.text}</p>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}

export default ChatBox;
