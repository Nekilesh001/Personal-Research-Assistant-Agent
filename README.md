# 🔬 Personal Research Assistant Agent

An AI-powered research agent that accepts a research query, fetches recent academic papers from multiple sources (arXiv + Semantic Scholar), embeds them into a vector store, and generates a structured research report using LLMs.

Built with a **LangChain ReAct (Reason + Act) agent** that thinks before acting, calls tools autonomously, loops until confident, and streams reasoning steps live to the frontend.


## ✨ Features

### Core
- **Query Understanding** — Agent parses vague queries intelligently
- **Query Expansion** — LLM rewrites vague queries into 2-3 specific search terms
- **Multi-Source Fetching** — arXiv + Semantic Scholar paper retrieval
- **Paper Embedding** — MiniLM converts abstracts to vectors (local, free)
- **ChromaDB Storage** — Persistent local vector store
- **MMR Retrieval** — Diverse + relevant chunk retrieval
- **CrossEncoder Re-ranking** — Re-ranks by true relevance
- **Structured Reports** — Overview, Key Papers, Findings, Gaps, Suggested Reading
- **Conversation Memory** — Retains context across queries in a session

### Quality
- **Advanced Filters** — Domain, keywords, date range, paper count, sort, source
- **Smart Defaults** — Auto-configured based on expert/beginner mode
- **LLM Fallback Chain** — Gemini → OpenAI → Ollama automatic failover
- **Download Reports** — Save as `.md` from the UI
- **Query History** — SQLite-backed, clickable sidebar

### Novel
- 🔥 **Contradiction Detector** — Finds papers with conflicting conclusions
- 💡 **Follow-up Suggester** — 3 clickable next questions after every report
- 🎯 **Expert / Beginner Mode** — Same data, two different report styles

### DevOps
- **Docker Compose** — One command runs the entire stack
- **Structured Logging** — Timestamps, levels, request IDs
- **SQLite Persistence** — Query history, sessions, saved reports

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, LangChain, Pydantic v2 |
| **LLM Providers** | Gemini 1.5 Flash, GPT-4o-mini, Llama3 (Ollama) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **Vector Store** | ChromaDB (persistent, local) |
| **Re-ranking** | CrossEncoder (ms-marco-MiniLM-L-6-v2) |
| **Paper Sources** | arXiv API, Semantic Scholar API |
| **Database** | SQLite via aiosqlite |
| **Frontend** | React 18, Vite, TailwindCSS |
| **Streaming** | Server-Sent Events (SSE) |
| **Containerization** | Docker + Docker Compose |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Google API key (for Gemini) — [get one free](https://makersuite.google.com/app/apikey)

### 1. Clone & Configure

```bash
git clone https://github.com/Nekilesh001/Personal-Research-Assistant-Agent.git
cd Personal-Research-Assistant-Agent
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 2. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The API will be available at `http://localhost:8000` (docs at `/docs`).

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

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
| `GET` | `/api/history` | Get query history |
| `GET` | `/api/report/{id}` | Get saved report |
| `DELETE` | `/api/history/{id}` | Delete history entry |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/domains` | List research domains |

### SSE Stream Events

```
data: {"type": "thought",       "content": "..."}
data: {"type": "action",        "content": "..."}
data: {"type": "observation",   "content": "..."}
data: {"type": "report",        "content": "...full markdown..."}
data: {"type": "followups",     "content": ["q1", "q2", "q3"]}
data: {"type": "contradictions", "content": [...]}
data: {"type": "done",          "content": ""}
```

---

## 📁 Project Structure

```
├── backend/
│   ├── src/              # Agent core, tools, generators
│   ├── models/           # LLM setup, Pydantic schemas
│   ├── utils/            # Vector store, DB, chunking, logging
│   ├── api/              # FastAPI routes
│   ├── data/             # Sample outputs
│   └── main.py           # Entry point
├── frontend/
│   ├── src/components/   # 7 React components
│   ├── src/App.jsx       # Main app with 3-panel layout
│   └── src/index.css     # Design system
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔧 Configuration

All configuration is via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `gemini` | Primary LLM (gemini/openai/ollama) |
| `GOOGLE_API_KEY` | — | Gemini API key |
| `OPENAI_API_KEY` | — | OpenAI API key (optional) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `LOG_LEVEL` | `INFO` | Logging level |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | Vector store path |
| `SQLITE_DB_PATH` | `./data/research_agent.db` | Database path |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built for the ML Internship Assessment at OneData Software Solutions.*
