# multi-agent-ai-research-assistant

# 🔬 Multi-Agent AI Research Assistant

An intelligent research assistant that uses **Multi-Agent AI, Retrieval-Augmented Generation (RAG), vector search, and Large Language Models (LLMs)** to help researchers analyze, compare, and understand research papers.

The system allows users to upload multiple research papers in PDF format and interact with them through specialized AI agents for **question answering, summarization, paper comparison, research-gap detection, and literature-review generation**.

---

## 🚀 Features

### 📄 Research Paper Upload

* Upload research papers in PDF format.
* Extract text page-by-page.
* Automatically split papers into smaller chunks.
* Preserve paper and page metadata.

### 🧠 RAG-Based Question Answering

* Convert document chunks into embeddings.
* Store embeddings in a persistent FAISS vector database.
* Retrieve the most relevant sections for each question.
* Generate answers using an LLM.
* Provide paper and page-level source citations.

### 🤖 Multi-Agent Architecture

The system contains specialized agents:

| Agent                   | Responsibility                                           |
| ----------------------- | -------------------------------------------------------- |
| Supervisor Agent        | Understands the query and routes it to the correct agent |
| QA Agent                | Answers questions about research papers                  |
| Summarization Agent     | Creates structured paper summaries                       |
| Comparison Agent        | Compares multiple research papers                        |
| Research Gap Agent      | Identifies limitations and research gaps                 |
| Literature Review Agent | Generates structured literature reviews                  |

### ⚖️ Paper Comparison

Compare multiple research papers based on:

* Research problem
* Objective
* Methodology
* Dataset
* Model/Algorithm
* Evaluation metrics
* Results
* Limitations

### 🔍 Research Gap Detection

The system identifies:

* Common limitations
* Dataset limitations
* Methodological gaps
* Performance gaps
* Evaluation gaps
* Real-world deployment limitations
* Potential future research directions

### 📚 Literature Review Generation

Generate structured literature reviews containing:

* Introduction
* Existing approaches
* Methodological comparison
* Major findings
* Limitations
* Research gaps
* Future research directions
* Conclusion

### 🔖 Source Citations

Answers can reference the original research paper and page:

```text
[Source: BERT.pdf, Page 5]
```

This helps users verify the generated information.

---

# 🏗️ System Architecture

```text
                         USER
                           │
                           ▼
                  React Frontend
                           │
                           ▼
                     FastAPI API
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
       Paper Processing             Research API
             │                           │
             ▼                           ▼
        PDF Extraction             Supervisor Agent
             │                           │
             ▼              ┌────────────┼────────────┐
        Text Chunking       │            │            │
             │              ▼            ▼            ▼
             ▼             QA       Comparison      Gap
        Embeddings          │            │            │
             │              └────────────┼────────────┘
             ▼                           │
       FAISS Vector Store               ▼
             │                     Literature
             │                        Agent
             └──────────────┬────────────┘
                            ▼
                           LLM
                            │
                            ▼
                   Answer + Citations
                            │
                            ▼
                     React Dashboard
```

---

# 🛠️ Technology Stack

## Frontend

* React.js
* Vite
* Axios
* CSS

## Backend

* Python
* FastAPI
* Uvicorn

## AI / ML

* Large Language Models
* LangGraph
* Sentence Transformers
* Retrieval-Augmented Generation (RAG)

## Vector Database

* FAISS

## PDF Processing

* PyMuPDF

## Database

* MongoDB
* PyMongo

## Authentication

* JWT
* Passlib

---

# 📁 Project Structure

```text
multi-agent-research-assistant/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatBox.jsx
│   │   │   ├── PaperUpload.jsx
│   │   │   └── PaperList.jsx
│   │   │
│   │   ├── pages/
│   │   │   └── Dashboard.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   │
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── supervisor.py
│   │   │   ├── summarizer.py
│   │   │   ├── qa_agent.py
│   │   │   ├── comparison_agent.py
│   │   │   ├── gap_agent.py
│   │   │   └── literature_agent.py
│   │   │
│   │   ├── rag/
│   │   │   ├── embeddings.py
│   │   │   ├── retriever.py
│   │   │   └── vector_store.py
│   │   │
│   │   ├── pdf/
│   │   │   ├── parser.py
│   │   │   └── chunker.py
│   │   │
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── papers.py
│   │   │   └── research.py
│   │   │
│   │   ├── database/
│   │   │   └── mongodb.py
│   │   │
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── .env
│
├── vector_store/
│
├── README.md
└── .gitignore
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/multi-agent-research-assistant.git

cd multi-agent-research-assistant
```

---

# 🐍 Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file inside the `backend` directory.

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=your_model_name

MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=research_assistant

JWT_SECRET=your_secret_key

VECTOR_STORE_PATH=../vector_store
```

### Important

Never commit `.env` to GitHub.

Add this to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
node_modules/
dist/
vector_store/
uploads/
```

---

# 🗄️ MongoDB Setup

You can use either:

### Local MongoDB

```text
mongodb://localhost:27017
```

or a MongoDB Atlas connection string.

The application uses the following collections:

```text
users
papers
research
```

---

# ▶️ Running the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The API will run at:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

---

# ⚛️ Frontend Setup

Open another terminal.

From the project root:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally run at:

```text
http://localhost:5173
```

---

# 🔄 How the System Works

## Step 1 — Upload Research Paper

User uploads:

```text
research-paper.pdf
```

↓

## Step 2 — PDF Processing

PyMuPDF extracts the text page-by-page.

```text
Page 1
Page 2
Page 3
...
```

↓

## Step 3 — Chunking

The extracted text is divided into smaller chunks.

```text
Page 1
 ├── Chunk 1
 ├── Chunk 2
 └── Chunk 3
```

↓

## Step 4 — Embeddings

Each chunk is converted into a numerical vector using a Sentence Transformer model.

↓

## Step 5 — FAISS

The vectors are stored in a persistent FAISS index.

Multiple papers can be stored:

```text
Paper A
Paper B
Paper C
Paper D
```

↓

## Step 6 — User Query

Example:

```text
What methodology was used in the papers?
```

↓

## Step 7 — Retrieval

The system retrieves the most relevant chunks.

↓

## Step 8 — Supervisor Agent

The supervisor determines which specialized agent should handle the request.

↓

## Step 9 — Specialized Agent

For example:

```text
Compare papers
        ↓
Comparison Agent
```

or:

```text
Find research gaps
        ↓
Research Gap Agent
```

↓

## Step 10 — LLM

The selected agent analyzes the retrieved context.

↓

## Step 11 — Final Response

The application returns:

```text
Answer

+
 
Source citations
```

Example:

```text
The proposed model uses a Transformer architecture.

[Source: research-paper.pdf, Page 5]
```

---

# 🧪 Example Queries

After uploading research papers, users can ask:

### Question Answering

```text
What methodology does Paper 1 use?
```

### Comparison

```text
Compare the methodologies used in all uploaded papers.
```

### Dataset Analysis

```text
Which datasets were used by the researchers?
```

### Research Gaps

```text
What are the major research gaps in these papers?
```

### Future Research

```text
What future research directions can be explored?
```

### Literature Review

```text
Generate a literature review based on these papers.
```

---

# 🤖 Multi-Agent Routing

The Supervisor Agent routes queries based on their intent.

```text
User Query
    │
    ▼
Supervisor
    │
    ├── Question → QA Agent
    │
    ├── Compare → Comparison Agent
    │
    ├── Research Gap → Gap Agent
    │
    └── Literature → Literature Agent
```

This allows the system to use the most appropriate agent for each task.

---

# 🔮 Future Enhancements

The current system provides the core RAG and multi-agent functionality. Future versions can include:

* [ ] Paper management dashboard
* [ ] Delete individual papers from vector storage
* [ ] User-specific vector databases
* [ ] Chat history
* [ ] Advanced authentication
* [ ] Research topic generator
* [ ] Knowledge graph
* [ ] Paper similarity detection
* [ ] Automatic reference extraction
* [ ] PDF/DOCX report generation
* [ ] RAG evaluation
* [ ] Agent performance evaluation
* [ ] Hallucination detection
* [ ] Streaming AI responses
* [ ] Cloud deployment
* [ ] Mobile-responsive interface

---

# 🔒 Security Considerations

The application should:

* Keep API keys in environment variables.
* Never commit `.env`.
* Validate uploaded files.
* Restrict upload sizes.
* Validate PDF content.
* Use JWT authentication for protected APIs.
* Separate user data.
* Apply appropriate CORS settings.
* Avoid exposing internal errors to users.

---

# 📈 Future Architecture

The planned production architecture is:

```text
                         React
                           │
                           ▼
                        FastAPI
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
          MongoDB       FAISS       Agent System
              │            │            │
              │            │       ┌────┴─────┐
              │            │       │          │
              │            │       ▼          ▼
              │            │      RAG      LLM
              │            │       │          │
              └────────────┼───────┴──────────┘
                           │
                           ▼
                    Final Response
                           │
                           ▼
                    Source Citations
```

---

# 🎯 Project Objectives

The main objectives of this project are:

1. Automate research-paper analysis.
2. Reduce the time required to understand academic literature.
3. Enable question answering over multiple research papers.
4. Compare methodologies and results across papers.
5. Identify research gaps automatically.
6. Generate structured literature reviews.
7. Provide evidence-backed answers with citations.
8. Demonstrate the practical use of multi-agent AI and RAG.

---

# 💡 Why This Project Is Different

Traditional PDF chatbots generally follow:

```text
PDF → LLM → Answer
```

This project uses:

```text
Multiple Papers
      ↓
PDF Processing
      ↓
Chunking
      ↓
Embeddings
      ↓
Persistent Vector Search
      ↓
RAG
      ↓
Supervisor Agent
      ↓
Specialized Research Agents
      ↓
LLM
      ↓
Verification
      ↓
Answer + Citations
```

This architecture makes the system more suitable for **academic research, literature analysis, and multi-document reasoning**.

---

# 👩‍💻 Author

**Sahasra Reddy**

B.Tech – Computer Science Engineering

---

# ⭐ Project Highlights

```text
✔ Multi-Agent AI
✔ LangGraph
✔ Retrieval-Augmented Generation
✔ FAISS Vector Search
✔ Sentence Transformers
✔ PDF Document Intelligence
✔ Multi-Paper Analysis
✔ Research Gap Detection
✔ Literature Review Generation
✔ Page-Level Citations
✔ FastAPI Backend
✔ React Frontend
✔ MongoDB
✔ JWT Authentication
```

---

## 📜 License

This project is intended for educational and research purposes. Add an appropriate open-source license before publicly distributing the project.
