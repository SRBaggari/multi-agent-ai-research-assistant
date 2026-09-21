import { useState } from "react";

import { deletePaper, getErrorMessage } from "../services/api";

function formatDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString();
}

function PaperList({
  papers,
  loading,
  error,
  indexedChunks,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  onChanged,
}) {
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState("");

  const remove = async (paper) => {
    const confirmed = window.confirm(
      `Delete "${paper.filename}"? Its chunks will be removed from the index.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(paper.paper_id);
      setDeleteError("");

      await deletePaper(paper.paper_id);

      if (onChanged) {
        onChanged();
      }
    } catch (requestError) {
      setDeleteError(getErrorMessage(requestError));
    } finally {
      setDeletingId(null);
    }
  };

  const allSelected =
    papers.length > 0 && selectedIds.length === papers.length;

  return (
    <div className="card">
      <h2>Uploaded papers</h2>

      {papers.length > 1 && (
        <div className="select-bar">
          <label className="inline">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={() => onSelectAll(!allSelected)}
              data-testid="select-all"
            />
            {allSelected ? "All papers selected" : "Select all"}
          </label>
          <span className="muted">
            {selectedIds.length} of {papers.length} selected
          </span>
        </div>
      )}

      {loading && <p className="muted">Loading papers...</p>}

      {error && (
        <div className="error" data-testid="papers-error">
          {error}
        </div>
      )}
      {deleteError && <div className="error">{deleteError}</div>}

      {/* The list comes from MongoDB but the index does not, so the two
          can disagree. Say so rather than showing a misleading "empty". */}
      {error && indexedChunks > 0 && (
        <p className="muted">
          The search index still holds {indexedChunks} chunk
          {indexedChunks === 1 ? "" : "s"}, so questions will still work.
        </p>
      )}

      {!loading && !error && papers.length === 0 && (
        <p className="muted" data-testid="papers-empty">
          No papers yet. Upload a PDF to start asking questions.
        </p>
      )}

      {papers.map((paper) => (
        <div className="paper" key={paper.paper_id} data-testid="paper-row">
          <input
            type="checkbox"
            className="paper-select"
            checked={selectedIds.includes(paper.paper_id)}
            onChange={() => onToggleSelect(paper.paper_id)}
            aria-label={`Include ${paper.filename} in questions`}
            data-testid="paper-checkbox"
          />

          <div className="paper-info">
            <strong>{paper.filename}</strong>
            <span className="muted">
              {paper.pages} pages &middot; {paper.chunks} chunks
              {paper.uploaded_at && ` · ${formatDate(paper.uploaded_at)}`}
            </span>
          </div>

          <button
            className="danger"
            onClick={() => remove(paper)}
            disabled={deletingId === paper.paper_id}
          >
            {deletingId === paper.paper_id ? "Deleting..." : "Delete"}
          </button>
        </div>
      ))}
    </div>
  );
}

export default PaperList;
