import { useCallback, useEffect, useState } from "react";

import PaperUpload from "../components/PaperUpload";
import PaperList from "../components/PaperList";
import ChatBox from "../components/ChatBox";

import { listPapers, checkHealth, getErrorMessage } from "../services/api";

function Dashboard({ user, onLogout }) {
  const [papers, setPapers] = useState([]);
  const [papersError, setPapersError] = useState("");
  const [loadingPapers, setLoadingPapers] = useState(true);

  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState("");

  // Which papers the next question applies to. Empty = all of them.
  const [selectedIds, setSelectedIds] = useState([]);

  // GET /health works even when MongoDB is down, so it is the reliable
  // way to know how many chunks are actually indexed.
  const refreshHealth = useCallback(async () => {
    try {
      setHealth(await checkHealth());
      setHealthError("");
    } catch (error) {
      setHealth(null);
      setHealthError(getErrorMessage(error));
    }
  }, []);

  const refreshPapers = useCallback(async () => {
    try {
      setLoadingPapers(true);
      setPapersError("");

      const data = await listPapers();
      const list = data.papers || [];
      setPapers(list);

      // Everything is selected by default, and papers that were deleted
      // are dropped from the selection.
      const ids = list.map((paper) => paper.paper_id);
      setSelectedIds((current) =>
        current.length === 0
          ? ids
          : current.filter((id) => ids.includes(id))
      );
    } catch (error) {
      setPapers([]);
      setPapersError(getErrorMessage(error));
    } finally {
      setLoadingPapers(false);
    }
  }, []);

  // useCallback so the effect below does not re-run on every render.
  const refreshAll = useCallback(async () => {
    // Run both: a MongoDB failure must not hide the health status.
    await Promise.all([refreshHealth(), refreshPapers()]);
  }, [refreshHealth, refreshPapers]);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const indexedChunks = health?.vector_store?.chunks ?? 0;

  const toggleSelect = (paperId) =>
    setSelectedIds((current) =>
      current.includes(paperId)
        ? current.filter((id) => id !== paperId)
        : [...current, paperId]
    );

  const selectAll = (select) =>
    setSelectedIds(select ? papers.map((paper) => paper.paper_id) : []);

  const selectedPapers = papers.filter((paper) =>
    selectedIds.includes(paper.paper_id)
  );

  return (
    <div className="dashboard">
      <header className="topbar">
        <div>
          <h1>AI Research Assistant</h1>
          <p className="muted">
            Analyse, compare and explore research papers with AI agents.
          </p>
        </div>

        <div className="topbar-right">
          {user?.email && <span className="muted">{user.email}</span>}
          <button
            className="secondary"
            onClick={onLogout}
            data-testid="logout-button"
          >
            Log out
          </button>
        </div>
      </header>

      {/* Status banners: tell the user which parts of the system are up. */}
      {healthError && (
        <div className="error banner" data-testid="health-error">
          {healthError}
        </div>
      )}

      {health && !health.database_connected && (
        <div className="warning banner" data-testid="db-warning">
          MongoDB is not connected. Sign-in, the paper list and history are
          unavailable, but uploading papers and asking questions still work.
        </div>
      )}

      {health && !health.openai_key_configured && (
        <div className="warning banner" data-testid="key-warning">
          No OpenAI API key is configured on the backend, so answers cannot be
          generated. Set OPENAI_API_KEY in backend/.env.
        </div>
      )}

      <main className="layout">
        <section className="column">
          <PaperUpload onUploaded={refreshAll} />

          <PaperList
            papers={papers}
            loading={loadingPapers}
            error={papersError}
            indexedChunks={indexedChunks}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onSelectAll={selectAll}
            onChanged={refreshAll}
          />
        </section>

        <section className="column wide">
          <ChatBox
            indexedChunks={indexedChunks}
            totalPapers={papers.length}
            selectedPapers={selectedPapers}
          />
        </section>
      </main>
    </div>
  );
}

export default Dashboard;
