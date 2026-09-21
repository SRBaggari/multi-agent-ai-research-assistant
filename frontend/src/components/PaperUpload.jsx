import { useRef, useState } from "react";

import { uploadPaper, getErrorMessage } from "../services/api";

function PaperUpload({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [warning, setWarning] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  const inputRef = useRef(null);

  const handleUpload = async () => {
    setStatus("");
    setWarning("");
    setError("");

    if (!file) {
      setError("Please select a PDF first.");
      return;
    }

    try {
      setUploading(true);

      const result = await uploadPaper(file);

      setStatus(
        `"${result.filename}" indexed: ` +
          `${result.pages} pages, ${result.chunks} chunks.`
      );

      // The upload itself succeeded, so a MongoDB problem is a warning,
      // not an error.
      if (result.warning) {
        setWarning(result.warning);
      }

      setFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }

      // Let the dashboard refresh the paper list.
      if (onUploaded) {
        onUploaded();
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card">
      <h2>Upload a paper</h2>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        data-testid="file-input"
        disabled={uploading}
        onChange={(event) => {
          setFile(event.target.files[0] || null);
          setStatus("");
          setWarning("");
          setError("");
        }}
      />

      <button
        onClick={handleUpload}
        disabled={uploading || !file}
        data-testid="upload-button"
      >
        {uploading ? "Indexing PDF..." : "Upload PDF"}
      </button>

      {uploading && (
        <p className="muted">
          Extracting text, creating chunks and building embeddings.
        </p>
      )}

      {status && (
        <div className="success" data-testid="upload-status">
          {status}
        </div>
      )}
      {warning && (
        <div className="warning spaced" data-testid="upload-warning">
          {warning}
        </div>
      )}
      {error && (
        <div className="error" role="alert" data-testid="upload-error">
          {error}
        </div>
      )}
    </div>
  );
}

export default PaperUpload;
