# 🔬 Personal Research Assistant Agent

An AI-powered research agent that accepts a research query, fetches recent academic papers from multiple sources (arXiv + Semantic Scholar), embeds them into a vector store, and generates a structured research report using LLMs.

Built with a **LangChain ReAct (Reason + Act) agent** that thinks before acting, calls tools autonomously, loops until confident, and streams reasoning steps live to the frontend.

---

## ✨ Features

### Core Research Pipeline
- **Query Understanding** — Agent parses vague queries intelligently
- **Query Expansion** — LLM rewrites vague queries into 2–3 specific search terms
- **Multi-Source Fetching** — arXiv + Semantic Scholar paper retrieval
- **Paper Embedding** — MiniLM converts abstracts to vectors (local, free)
- **ChromaDB Storage** — Persistent local vector store with deduplication
- **MMR Retrieval** — Diverse + relevant chunk retrieval with metadata filtering
- **CrossEncoder Re-ranking** — Re-ranks by true relevance
- **Structured Reports** — Overview, Key Papers, Findings, Gaps, Suggested Reading

### PDF Upload & Analysis
- **Upload Your Own PDFs** — Upload up to 5 local research papers (max 10 MB each)
- **Full Text Extraction** — Extracts and chunks PDF content using PyMuPDF
- **Source-Filtered Retrieval** — When using uploaded papers, only those chunks are retrieved (no mixing with arXiv results)
- **Automatic Report Generation** — Report is triggered immediately after upload, referencing the actual paper title

### Chatbot
- **Per-Report Chat** — Chat with the AI about any generated report
- **Persistent Chat Memory** — Conversations are saved to SQLite and survive server restarts
- **Context-Aware** — AI answers strictly from the papers in the report and cites sources

### History
- **Full Research History** — All queries and reports saved to SQLite, grouped by date
- **Chat Transcript Viewer** — Expand any history item to see the full chat conversation
- **One-Click Report Reload** — "View Report →" button navigates back to a past report

### Quality
- **Advanced Filters** — Domain, keywords, date range, paper count, sort order, source
- **Expert / Beginner Mode** — Same data, two different report styles
- **LLM Fallback Chain** — Groq → OpenAI → Ollama automatic failover
- **Rate Limit Fallback** — Automatically switches to local Ollama when Groq hits quota (429)
- **PDF Report Download** — Save generated reports as `.pdf` from the UI
- **Contradiction Detector** — Finds papers with conflicting conclusions
- **Follow-up Suggester** — 3 clickable next questions after every report

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, LangChain, Pydantic v2 |
| **LLM Providers** | Groq (llama-3.3-70b-versatile), OpenAI GPT-4o-mini, Ollama (local) |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`, local/free) |
| **Vector Store** | ChromaDB (persistent, local, source-filtered) |
| **Re-ranking** | CrossEncoder (`ms-marco-MiniLM-L-6-v2`) |
| **PDF Parsing** | PyMuPDF (fitz) |
| **Paper Sources** | arXiv API, Semantic Scholar API |
| **Database** | SQLite via aiosqlite (queries, reports, chat messages) |
| **Frontend** | React 18, Vite, TailwindCSS |
| **Streaming** | Server-Sent Events (SSE) |
| **Containerization** | Docker + Docker Compose |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A [Groq API key](https://console.groq.com) (free tier available)

### 1. Clone & Configure

```bash
git clone https://github.com/Nekilesh001/Personal-Research-Assistant-Agent.git
cd Personal-Research-Assistant-Agent
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Start Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python main.py
```

API available at `http://localhost:8000` (Swagger docs at `/docs`).

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### 4. Or Use Docker (one command)

```bash
cp .env.example .env
# Edit .env with your API key
docker-compose up --build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/query` | Run research agent (SSE stream) |
| `POST` | `/api/query-uploaded` | Run pipeline on uploaded PDFs only |
| `POST` | `/api/upload-papers` | Upload PDF files for analysis |
| `POST` | `/api/search-papers` | Search papers without LLM (no tokens) |
| `GET` | `/api/history` | Get query history |
| `GET` | `/api/report/{id}` | Get saved report |
| `DELETE` | `/api/history/{id}` | Delete history entry |
| `POST` | `/api/chat/{query_id}` | Chat with a report (SSE stream) |
| `GET` | `/api/chat/{query_id}/history` | Get persisted chat history |
| `DELETE` | `/api/chat/{query_id}/history` | Clear chat history |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/test-llm` | Test LLM connection |
| `GET` | `/api/domains` | List research domains |

### SSE Stream Events

```
data: {"type": "thought",        "content": "..."}
data: {"type": "action",         "content": "..."}
data: {"type": "observation",    "content": "..."}
data: {"type": "report",         "content": "...full markdown..."}
data: {"type": "followups",      "content": ["q1", "q2", "q3"]}
data: {"type": "contradictions", "content": [...]}
data: {"type": "done",           "content": ""}
```

---

## 📁 Project Structure

```
├── backend/
│   ├── src/
│   │   ├── agent.py              # ReAct pipeline orchestrator
│   │   ├── tools.py              # arXiv, Semantic Scholar, vector store tools
│   │   ├── chat_handler.py       # Chatbot with persistent SQLite memory
│   │   ├── report_generator.py   # LLM report synthesis
│   │   ├── contradiction_detector.py
│   │   └── followup_generator.py
│   ├── models/
│   │   ├── llm_setup.py          # Groq→OpenAI→Ollama fallback chain
│   │   └── schemas.py            # Pydantic request/response models
│   ├── utils/
│   │   ├── vector_store.py       # ChromaDB operations (with source filtering)
│   │   ├── db.py                 # SQLite: queries, reports, chat_messages
│   │   ├── chunker.py            # Token-aware text chunking
│   │   ├── pdf_extractor.py      # PyMuPDF PDF parsing
│   │   └── logger.py
│   ├── api/
│   │   └── routes.py             # All FastAPI route definitions
│   └── main.py                   # Entry point
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ResearchPage.jsx  # Main research + upload interface
│   │   │   ├── HistoryPage.jsx   # History with chat transcript viewer
│   │   │   └── UploadPage.jsx
│   │   ├── components/           # ReportViewer, FilterPanel, ChatPanel, etc.
│   │   └── App.jsx
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 🔧 Configuration

All configuration is via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | Primary LLM provider (`groq`/`openai`/`ollama`) |
| `GROQ_API_KEY` | — | Groq API key (free at console.groq.com) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `OPENAI_API_KEY` | — | OpenAI API key (optional fallback) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server URL |
| `OLLAMA_MODEL` | `gemma3:12b` | Ollama model name |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | Vector store path |
| `SQLITE_DB_PATH` | `./data/research_agent.db` | Database path |
| `LOG_LEVEL` | `INFO` | Logging level |

### LLM Fallback Behaviour

The system automatically falls back across providers:
1. **Groq** — Primary (fastest, free tier)
2. **OpenAI** — If Groq key is missing
3. **Ollama** — Local fallback; also triggers automatically when Groq returns a **429 rate limit** error

---

## 🗄 Database Schema

```
queries        — query_id, query, mode, filters, paper_count, timestamps
reports        — report_id, query_id, report_markdown, contradictions, followups, papers
chat_messages  — id, query_id, role, content, created_at
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built for the ML Internship Assessment at OneData Software Solutions.*
