# EchoMind — Human Digital Twin Intelligence Platform

<div align="center">

![EchoMind](https://img.shields.io/badge/EchoMind-v1.0.0-6366f1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIiBmaWxsPSIjNjM2NmYxIi8+PC9zdmc+)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript)

**Not a chatbot. Not RAG. A true Human Digital Twin Intelligence Platform.**

</div>

---

## 🧠 What is EchoMind?

EchoMind creates an AI-based digital twin of a person that:

- **Learns** from conversations, notes, documents, and behavioral patterns
- **Thinks** similarly to the user
- **Writes** similarly to the user
- **Predicts** future decisions with confidence scores
- **Simulates** alternative life paths and scenarios
- **Evolves** continuously as more data is ingested

Think: *Black Mirror + AI Memory + Personal Knowledge Graph + Digital Identity Engine*

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + TS + Tailwind)       │
│  Dashboard │ Twin Chat │ Memory │ Personality │ Graph     │
├─────────────────────────────────────────────────────────┤
│                    Backend (FastAPI + Python)              │
│  Auth │ Ingestion │ Twin │ Memory │ Predict │ Simulate    │
├─────────────────────────────────────────────────────────┤
│                    AI Layer (LangChain + LLMs)            │
│  Personality │ Behavior │ Communication │ Emotional       │
│  Prediction │ Simulation │ Memory │ Knowledge Graph       │
├────────────┬────────────┬────────────┬──────────────────┤
│ PostgreSQL │   Neo4j    │  ChromaDB  │      Redis       │
│ (Structured)│  (Graph)  │  (Vectors) │     (Cache)      │
└────────────┴────────────┴────────────┴──────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Launch all services
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/docs
# Neo4j Browser: http://localhost:7474
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Required Services:**
- PostgreSQL 16+ on port 5432
- Redis 7+ on port 6379
- Neo4j 5+ on port 7687
- ChromaDB on port 8001

---

## 📱 UI Pages (10)

| Page | Description |
|------|-------------|
| **Dashboard** | Command center with accuracy scores, charts, and system status |
| **Digital Twin Chat** | Chat interface with real-time confidence and personality matching |
| **Memory Vault** | Browse, search, and manage 5 types of long-term memories |
| **Personality Engine** | Big Five radar, tone profile, writing style, beliefs, interests |
| **Behavior Analytics** | Decision patterns, risk tolerance, habits, productivity |
| **Future Simulator** | Predict decisions and simulate future outcomes with probabilities |
| **Knowledge Graph** | Interactive graph of people, projects, events, and relationships |
| **Emotional Insights** | Mood tracking, emotional radar, pattern detection |
| **Life Timeline** | Vertical scrolling timeline of key events and milestones |
| **Settings** | Data upload, API configuration, privacy controls |

---

## 🤖 AI Engines (10)

1. **Personality Learning Engine** — Big Five, writing style, tone, beliefs extraction
2. **Behavioral Modeling Engine** — Decision patterns, risk tolerance, habits
3. **Digital Twin Generator** — Personality-matched response generation
4. **Long-Term Memory System** — 5 memory types with importance scoring
5. **Decision Prediction Engine** — Scenario-based prediction with confidence
6. **Future Self Simulator** — Monte Carlo-style outcome simulation
7. **Communication Cloning** — Writing style fingerprinting and transfer
8. **Emotional Intelligence Engine** — 8 emotion detection, mood profiles
9. **Knowledge Graph Engine** — Entity extraction and relationship inference
10. **Digital Legacy System** — Timeline generation and life summaries

---

## 🗃️ Database Schema

| Table | Records |
|-------|---------|
| `users` | User accounts and settings |
| `memories` | 5-type long-term memory storage |
| `conversations` | Twin chat sessions with scoring |
| `documents` | Uploaded documents with processing status |
| `personality_profiles` | Evolving Big Five + writing style profiles |
| `behavior_profiles` | Decision patterns and behavioral traits |
| `predictions` | Decision predictions with confidence |
| `simulations` | Future scenario simulations |
| `knowledge_graph_nodes` | Entity nodes (people, projects, events...) |
| `knowledge_graph_edges` | Relationship edges between entities |
| `analytics` | Platform metrics and scoring over time |

---

## 🔐 Security

- JWT-based authentication with bcrypt password hashing
- Encrypted memory storage
- User-controlled data deletion
- Role-based access control
- Secure document storage

---

## 📊 Scoring System

- **Twin Accuracy Score** — Overall fidelity of the digital twin
- **Personality Consistency Score** — Profile reliability over time
- **Decision Prediction Accuracy** — Historical prediction correctness
- **Memory Recall Accuracy** — Relevance of retrieved memories
- **Communication Similarity Score** — Writing style match
- **Behavior Match Score** — Behavioral alignment

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11, SQLAlchemy, Pydantic |
| AI | LangChain, OpenAI GPT-4, Sentence Transformers |
| Database | PostgreSQL 16 |
| Vector DB | ChromaDB + FAISS |
| Graph DB | Neo4j 5 |
| Cache | Redis 7 |
| Deployment | Docker, Docker Compose, AWS |

---

## 📄 License

MIT License — Build the future of human digital identity.

---

<div align="center">

**EchoMind** — *The world's first true Human Digital Twin Platform.*

</div>
