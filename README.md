# Multi-Agent AI Research Assistant

## Project Overview

A research assistant that reads your research papers and answers questions about
them, with citations back to the exact page.

It:

- accepts research papers as PDF uploads
- extracts the text page by page with PyMuPDF
- splits the text into overlapping chunks that remember their page number
- generates embeddings with a Sentence-Transformer model
- stores and searches those vectors in a FAISS index that persists to disk
- retrieves the chunks most relevant to your question
- routes the question to a specialised agent through a LangGraph supervisor
- generates the answer with an OpenAI model using only the retrieved context
- returns the sources with filename and page number
- provides a React dashboard for uploading, asking, and reviewing sources

---

## Architecture

```
React frontend (Vite)
        |
        v
FastAPI backend
        |
        v
RAG layer  ->  PyMuPDF -> chunker -> Sentence-Transformers -> FAISS
        |
        v
LangGraph Supervisor  (classifies the question)
        |
        v
Specialised Agents  (QA | Comparison | Gap | Literature | Summarizer)
        |
        v
OpenAI  ->  answer + sources  ->  back to the frontend
```

The supervisor imports the agents, and every agent gets its OpenAI access from
`app/agents/llm.py`. No agent imports the supervisor, which is what keeps the
import graph acyclic.

---

## Agents

| Agent | Handles | Example question |
|---|---|---|
| **QA** | Factual questions about the papers. The default. | "What is the main contribution of this paper?" |
| **Comparison** | Comparing or contrasting papers, methods or results. | "Compare the methodology of these papers." |
| **Research Gap** | Limitations, gaps, open problems, future work. | "What are the research gaps?" |
| **Literature Review** | A structured review or related-work overview. | "Give me a literature review." |
| **Summarizer** | A summary or overview of a paper. | "Summarize this paper." |

The supervisor classifies by whole-word phrase matching, so variations work:
`compare / comparison / difference / differ / versus / vs`,
`research gap / limitation / future work / open problems`,
`literature review / related work / prior work / state of the art`,
`summary / summarize / overview / abstract / key takeaways`.
Anything else falls through to QA.

`gap` is checked before `comparison`, so "compare the research gaps" is still
treated as a gap question.

Setting `USE_LLM_ROUTER=true` lets the model classify questions that match no
keyword. It is off by default so routing stays deterministic, fast and free; if
the call fails, routing falls back to QA.

---

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10 or newer | Verified on 3.14 |
| Node.js | 18 or newer | Verified on 24 |
| MongoDB | 6 or newer | Local install or MongoDB Atlas |
| OpenAI API key | — | Needed for answers; everything else works without it |

---

## Backend setup

Exact commands for Windows PowerShell, from the project root:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
```

Then open `backend\.env` and fill in your own values (see
[Environment variables](#environment-variables)).

If PowerShell blocks the activate script, allow it for the current user once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Using Git Bash instead of PowerShell, activate with:

```bash
source .venv/Scripts/activate
```

> The install downloads PyTorch and is a few hundred megabytes. The first PDF
> upload additionally downloads the embedding model (~90 MB) once.

---

## Frontend setup

```powershell
cd frontend
npm install
copy .env.example .env
```

---

## Environment variables

### `backend/.env`

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI key. Required for generating answers. |
| `OPENAI_MODEL` | A model your key can use, e.g. `gpt-4o-mini`. |
| `OPENAI_BASE_URL` | Optional. Blank = OpenAI. Set it to any OpenAI-compatible endpoint to use another provider. |
| `MONGO_URI` | MongoDB connection string. |
| `DATABASE_NAME` | Database name, default `research_assistant`. |
| `JWT_SECRET` | Any long random string used to sign login tokens. |
| `JWT_EXPIRE_DAYS` | Token lifetime in days, default `1`. |
| `VECTOR_STORE_PATH` | Where the FAISS index lives. Relative paths resolve from the project root, not your terminal. |
| `EMBEDDING_MODEL` | Sentence-Transformer model, default `all-MiniLM-L6-v2`. |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Chunking settings, default `1200` / `200`. |
| `USE_LLM_ROUTER` | `true` to let the LLM classify unmatched questions. |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins. |

### `frontend/.env`

| Variable | Purpose |
|---|---|
| `VITE_API_URL` | Base URL of the backend, e.g. `http://localhost:8000`. |

Both `.env` files are git-ignored. Only the `.env.example` templates are
committed, and they contain placeholders only. **Never put a real API key in
this README, in source code, or in `.env.example`.**

Vite reads `.env` at start-up only, so restart `npm run dev` after changing it.

---

## Running the project

Two terminals.

**Terminal 1 — backend:**

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --reload-dir app
```

`--reload-dir app` keeps the auto-reloader watching your own code only.
Without it, uvicorn also watches `.venv` and restarts whenever it notices a
package file, which reloads the embedding model for no reason.

- API: <http://127.0.0.1:8000>
- Swagger docs: <http://127.0.0.1:8000/docs>

**Terminal 2 — frontend:**

```powershell
cd frontend
npm run dev
```

- App: <http://localhost:5173>

Then register an account, upload a PDF, and ask a question.

To produce a production build of the frontend:

```powershell
cd frontend
npm run build
```

---

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | API banner |
| GET | `/health` | Database, OpenAI and vector store status |
| POST | `/auth/register` | Create an account, returns a JWT |
| POST | `/auth/login` | Log in, returns a JWT |
| GET | `/auth/me` | Current user (requires `Authorization: Bearer <token>`) |
| POST | `/papers/upload` | Upload and index a PDF |
| GET | `/papers` | List uploaded papers |
| GET | `/papers/{paper_id}` | One paper's details |
| DELETE | `/papers/{paper_id}` | Delete a paper, its chunks and its file |
| POST | `/research/ask` | Ask a research question |
| GET | `/research/history` | Recent questions and answers |

### `POST /research/ask`

Request:

```json
{
  "query": "What is the main contribution of the paper?",
  "top_k": 6
}
```

Response:

```json
{
  "query": "What is the main contribution of the paper?",
  "agent": "qa",
  "answer": "The paper's main contribution is ...",
  "sources": [
    {
      "paper_id": "0f9c...",
      "filename": "paper.pdf",
      "page_number": 4,
      "text": "...",
      "score": 0.7421
    }
  ]
}
```

Error responses:

| Status | Meaning |
|---|---|
| 400 | Empty question, or no papers uploaded yet |
| 401 | Missing or invalid authentication token |
| 404 | Nothing relevant found in the uploaded papers |
| 422 | `top_k` out of range (1–20), or a missing field |
| 500 | Embedding, vector store or database failure |
| 502 | LLM failure: bad API key, unknown model, quota or network |

Authentication is **optional** on `/papers/*` and `/research/ask`: send a Bearer
token and the activity is attributed to that user, or call them anonymously from
Swagger. `/auth/me` always requires a token.

---

## Using a different LLM provider

The project talks to OpenAI by default. Because the OpenAI SDK can point at
any OpenAI-compatible endpoint, you can switch provider with two settings and
no code changes — useful if your OpenAI account has no credits.

In `backend\.env`:

```
# Groq (free tier)
OPENAI_API_KEY=gsk_your_groq_key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
```

```
# OpenRouter (has free models)
OPENAI_API_KEY=sk-or-your_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

Then restart the backend. Leave `OPENAI_BASE_URL` blank to go back to OpenAI.

`OPENAI_MODEL` must name a model the chosen provider actually offers; if it
does not, `/research/ask` returns a 502 naming the model and the endpoint.

Only the answer-generation step changes. Embeddings stay local
(Sentence-Transformers), so retrieval and citations are unaffected.

---

## RAG pipeline

```
PDF -> PyMuPDF -> chunks -> embeddings -> FAISS -> retrieval -> agent -> answer
```

1. **PDF** — `POST /papers/upload` checks the file really is a PDF (magic bytes,
   not just the extension) and saves it under a generated `paper_id`.
2. **PyMuPDF** — text is extracted page by page. Pages with no text layer are
   skipped, but the remaining page numbers stay correct, so citations point at
   the right page of the original document.
3. **Chunks** — each page is split into ~1200-character chunks with a
   200-character overlap. Every chunk carries `paper_id`, `filename` and
   `page_number`.
4. **Embeddings** — `all-MiniLM-L6-v2` turns each chunk into a normalised
   384-dimension vector. The model is loaded once and shared.
5. **FAISS** — vectors go into an `IndexFlatL2`. The index, the chunk texts and
   the metadata are written to `vector_store/` as `research.index`,
   `documents.pkl` and `metadata.pkl`, and reloaded on start-up.
6. **Retrieval** — the question is embedded the same way and FAISS returns the
   `top_k` nearest chunks. `top_k` is clamped to the number of stored chunks.
7. **Agent** — the chunks become the agent's context, each prefixed with
   `SOURCE:` and `PAGE:`. The supervisor picks the agent; the agent calls OpenAI.
8. **Answer** — the answer plus the same chunks are returned as `sources`.

Uploading and searching share one vector store instance, so a paper is
searchable the moment its upload returns.

---

## Troubleshooting

**MongoDB not running**

Symptoms: register and login return
`"Could not reach the database. Is MongoDB running?"`; `GET /papers` returns 500;
the dashboard shows an amber "MongoDB is not connected" banner.

Uploading papers and asking questions still work — only accounts, the paper list
and history need MongoDB. Start the MongoDB service, or point `MONGO_URI` at a
MongoDB Atlas cluster. Check with `GET /health` → `"database_connected": true`.

Note: while MongoDB is unreachable, `/health` takes about 5 seconds because it
waits for the connection attempt to time out. This disappears once it is running.

**OpenAI API key missing or invalid**

`POST /research/ask` returns **502**:

- `"OpenAI rejected the API key (401)"` — `OPENAI_API_KEY` is missing, still a
  placeholder, or wrong.
- `"The model '...' is not available for this API key"` — set `OPENAI_MODEL` to a
  model your account can reach, such as `gpt-4o-mini`.
- `"rate limit reached or the account has no remaining quota"` — billing issue.

Retrieval still works; only the generation step fails.

**Port already in use**

`[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`
means something already listens on that port. Find and stop it:

```powershell
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

Or run on another port and update `frontend\.env` to match:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

For Vite: `npm run dev -- --port 5174`.

**Empty vector store**

`POST /research/ask` returns **400**
`"No research papers have been uploaded yet."` — nothing is indexed. Upload a PDF
first. `GET /health` shows how many chunks and papers the index holds.

If you see `"The vector store files are inconsistent"`, the three files in
`vector_store/` are out of sync. Stop the backend, delete the folder's contents,
restart, and re-upload.

**PDF upload errors**

| Message | Cause |
|---|---|
| `Only PDF files are supported.` | The file is not a `.pdf`. |
| `This file is not a valid PDF.` | The contents are not a real PDF. |
| `The uploaded file is empty.` | Zero bytes. |
| `The PDF is larger than the 50 MB limit.` | Too large. |
| `No text could be extracted from this PDF.` | A scan or image-only PDF. There is no OCR step. |
| `This PDF is password protected` | Remove the password first. |

**Frontend shows "Could not reach the server"**

The backend is not running, or `VITE_API_URL` points elsewhere. Restart
`npm run dev` after changing `.env`.

**CORS error in the browser console**

Add your frontend origin to `CORS_ORIGINS` in `backend\.env`, comma separated.

**`ImportError: cannot import name 'ask_llm'`**

An agent is importing from `supervisor` instead of `llm`. Every agent must use
`from app.agents.llm import ask_llm`.

---

## Current limitations

Being honest about what this project does and does not do:

- **No OCR.** Scanned or image-only PDFs cannot be indexed.
- **Papers are global, not per-user.** Authentication works and activity is
  attributed to a user, but every account searches the same index. Auth is
  optional on the paper and research endpoints so Swagger stays usable.
- **No paper filtering.** A question searches every uploaded paper; you cannot
  restrict it to a chosen subset.
- **Flat FAISS index.** `IndexFlatL2` is exact but scans everything, so search
  slows down once the corpus grows large.
- **Deleting rebuilds the index.** Fine at this scale, but O(n) per delete.
- **No reranking.** The chunks nearest in embedding space go straight to the
  agent.
- **Answers are not streamed.** The UI waits for the complete response.
- **In-memory vector store, single process.** Running uvicorn with multiple
  workers would give each worker its own copy.
- **No automated test suite in the repository.** The project was verified with
  external test scripts, not committed pytest/vitest files.
- **`/health` is slow while MongoDB is down** (~5s), as described above.
