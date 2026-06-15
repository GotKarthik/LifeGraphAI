# LifeGraphAI

> An encrypted, AI-powered personal journaling platform that acts as an introspective reflection engine — knowing who you are, grounded strictly in what you've written.

## What It Does

You write journal entries. LifeGraphAI reads them, encrypts them, processes them through a multi-stage AI pipeline, and answers questions about your own life — with citations back to the exact entries that support every claim. No hallucination. No generic advice. Just your own patterns, reflected back at you.

**Example:**
> *"Do I love Amy?"*
> "You haven't written the word 'love' anywhere in your entries — but your entries tell a more complicated story. You described Amy as 'the only person in my immediate social circle who can follow my train of thought past the third station' [Day 2]. When you found an error in your published paper, she was the first person you called [Day 5]..."

---

## Architecture
User Query

↓

Hybrid Search (retrieval.py)

├── pgvector cosine similarity (BGE-M3 embeddings)

└── JSONB keyword / entity lookup

↓

Pass 1 — Local Qwen 1.5B (Chain-of-Thought analysis)

↓

Pass 2 — Gemini 2.5 Flash (Grounded synthesis + citation enforcement)

↓

Cited, second-person response streamed to frontend

### Full Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, Tailwind CSS, React Query |
| Backend API | FastAPI, Python |
| Database | PostgreSQL + pgvector |
| Async Pipeline | Celery + Redis |
| Local Embedding | BAAI/bge-m3 (HuggingFace) |
| Local Reasoning | Qwen/Qwen2.5-1.5B-Instruct |
| Cloud Synthesis | Gemini 2.5 Flash |
| Security | AES-256-GCM field-level encryption, bcrypt, JWT |
| Infrastructure | Docker Compose |

---

## Key Features

**Hybrid RAG Pipeline** — Combines pgvector semantic similarity search with structured JSONB entity/topic lookups. Finds entries by meaning AND by named entities (people, places) extracted during ingestion.

**Two-Pass Agent Architecture** — Pass 1 uses a local 1.5B model for chain-of-thought fact extraction from retrieved chunks. Pass 2 sends the extracted facts + context to Gemini Flash for grounded synthesis. This keeps API costs low while achieving high answer quality.

**Field-Level Encryption** — All journal text is encrypted with AES-256-GCM before being written to PostgreSQL. The plaintext never touches the database. Decryption happens in memory inside the Celery worker during AI processing.

**Async Processing** — Saving a journal entry returns immediately. Celery picks up the background task: decrypt → chunk → embed (BGE-M3) → extract entities/emotions/topics (Gemini) → store vectors → mark complete. Zero perceived latency.

**Personalized Agent Persona** — User name and bio are injected directly into the agent system prompt. The AI addresses you by name, in second person, with awareness of who you are. Eliminates third-person "narrator" hallucinations entirely.

**Entity Co-occurrence Graph** — Tracks how people, places, and topics appear together across entries. Surfaces relationship patterns and renders a mood timeline via Recharts.

---

## Setup

### Prerequisites
- Docker + Docker Compose
- Python 3.11+
- Node.js 18+
- Gemini API key (free tier: 1500 requests/day)

### Run

```bash
# 1. Clone and configure
git clone https://github.com/GotKarthik/LifeGraphAI.git
cd LifeGraphAI
cp .env.example .env
# Fill in GEMINI_API_KEY, SECRET_KEY in .env

# 2. Start everything
./start.sh

# 3. Open
http://localhost:3000
```

On first run, register an account, go to Settings, and add your name and a short bio. This is what the AI uses to address you personally.

---

## Project Structure
apps/

├── web/                    # Next.js 15 frontend

│   └── src/app/

│       ├── dashboard/      # Main journal view

│       ├── journals/       # New entry + individual entry pages

│       ├── reflection/     # Ask AI interface

│       ├── timeline/       # Mood graph + entity timeline

│       └── settings/       # Profile / bio management

└── api/                    # FastAPI backend

├── main.py

├── api/v1/endpoints/   # Auth, journals, memory, users

├── core/

│   ├── agent.py        # Two-pass reflection agent

│   ├── retrieval.py    # Hybrid pgvector + JSONB search

│   ├── tasks.py        # Celery background pipeline

│   ├── ai.py           # BGE-M3 embedding

│   ├── llm.py          # Entity/emotion extraction

│   ├── encryption.py   # AES-256-GCM

│   └── graph.py        # Co-occurrence graph construction

└── models/             # SQLAlchemy models

---

## How the AI Pipeline Works

1. **Write** a journal entry → frontend sends to `POST /api/v1/journals`
2. **Encrypt** → AES-256-GCM, stored in PostgreSQL
3. **Queue** → `process_journal_entry.delay(journal_id)` sent to Celery via Redis
4. **Process** (background):
   - Decrypt into memory
   - Chunk into 500-token segments
   - Embed each chunk with BGE-M3 → store in pgvector
   - Extract `topics`, `entities`, `emotions`, `action_items` via Gemini → store as JSONB
   - Flip status to `completed`
5. **Ask** a question → hybrid search retrieves top-K chunks → Pass 1 analysis → Pass 2 synthesis → cited answer streamed to UI

---

## Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost:5432/lifegraphai
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-jwt-secret-key
GEMINI_API_KEY=your-gemini-api-key
ENCRYPTION_KEY=your-32-byte-aes-key
```

---

*Built by [Karthik](https://github.com/GotKarthik)*
