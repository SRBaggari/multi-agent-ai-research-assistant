
import { useState } from "react";

import { uploadPaper } from "../services/api";


function PaperUpload() {

  const [file, setFile] = useState(null);

  const [message, setMessage] = useState("");


  const handleUpload = async () => {

    if (!file) {

      setMessage(
        "Please select a PDF first."
      );

      return;
    }

    try {

      setMessage("Uploading...");

      const result =
        await uploadPaper(file);

      setMessage(
        `Uploaded successfully. ${result.chunks} chunks created.`
      );

    } catch (error) {

      console.error(error);

      setMessage(
        "Upload failed."
      );
    }
  };


  return (

    <div className="card">

      <h2>Upload Research Paper</h2>

      <input
        type="file"
        accept=".pdf"
        onChange={(event) =>
          setFile(event.target.files[0])
        }
      />

      <button
        onClick={handleUpload}
      >
        Upload PDF
      </button>

      {message && (
        <p>{message}</p>
      )}

    </div>
  );
}


export default PaperUpload;