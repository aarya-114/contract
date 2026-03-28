# ContractSense ⚖️
### AI-Powered Contract Risk Analysis

ContractSense analyzes legal contracts and identifies risky clauses using RAG (Retrieval Augmented Generation). Upload any contract PDF and get instant risk analysis with plain English explanations, negotiation suggestions, and visual highlights on the original document.

---

## 🎯 What It Does

- **Parses** any contract PDF and extracts clauses intelligently
- **Analyzes** each clause using AI (Groq llama-3.1-8b) with RAG
- **Classifies** clauses as Safe 🟢, Caution 🟡, or Risky 🔴
- **Explains** each clause in plain English
- **Suggests** negotiation points for risky clauses
- **Highlights** exact clause locations on the original PDF

---

## 🏗️ Architecture
```
PDF Upload → PyMuPDF Parser → Clause Segmenter
                                      ↓
                            sentence-transformers
                            (384-dim embeddings)
                                      ↓
                              ChromaDB Vector Store
                              ┌───────────────────┐
                              │ knowledge_base     │ ← Standard templates
                              │ active_contract    │ ← Uploaded contract
                              └───────────────────┘
                                      ↓
                              RAG Retrieval
                              (find similar standard clause)
                                      ↓
                              Groq llama-3.1-8b
                              (risk classification)
                                      ↓
                    ┌─────────────────────────────────┐
                    │  Risk Report + PDF Highlights    │
                    │  session stored in Redis (1hr)   │
                    └─────────────────────────────────┘
                                      ↓
                              React Frontend
                         PDF Viewer + Clause List
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | FastAPI (Python) | REST API |
| PDF Parsing | PyMuPDF | Text extraction + coordinates |
| Embeddings | sentence-transformers | Text → vectors (local, free) |
| Vector DB | ChromaDB | Semantic search |
| LLM | Groq llama-3.1-8b | Risk classification |
| Cache | Redis | PDF storage + session management |
| Frontend | React + Vite + Tailwind | UI |
| PDF Viewer | react-pdf | In-browser PDF rendering |
| Container | Docker + Docker Compose | Reproducible environment |

---

## 🧠 How RAG Works Here

Instead of asking the AI "is this clause risky?" in isolation, ContractSense:

1. Embeds the clause into a 384-dimensional vector
2. Searches a knowledge base of 19 standard contract templates
3. Finds the most similar standard clause (cosine similarity)
4. Sends BOTH to the LLM: "Compare my clause against this standard. Is it risky?"

This grounds the AI's analysis in real reference material, preventing hallucination.

---

## 📁 Project Structure
```
contractsense/
├── backend/
│   ├── main.py                  # FastAPI app + startup
│   ├── routers/
│   │   ├── upload.py            # POST /upload
│   │   ├── analyze.py           # POST /analyze (full pipeline)
│   │   ├── search.py            # POST /search/similar
│   │   └── pdf_viewer.py        # GET /pdf/{session_id}
│   ├── services/
│   │   ├── pdf_parser.py        # PDF extraction + clause location
│   │   ├── segmenter.py         # Clause boundary detection
│   │   ├── embedder.py          # sentence-transformers wrapper
│   │   ├── vector_store.py      # ChromaDB operations
│   │   └── analyzer.py          # Groq + RAG analysis
│   ├── core/
│   │   ├── config.py            # Pydantic settings
│   │   ├── redis_client.py      # Redis connection
│   │   └── chroma_client.py     # ChromaDB connection
│   ├── knowledge_base/
│   │   └── templates.py         # 19 standard contract templates
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main React app
│   │   └── components/
│   │       └── PDFViewer.jsx    # PDF rendering + highlights
│   └── vite.config.js
└── docker-compose.yml
```

---

## 🚀 Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- Groq API key (free at console.groq.com)

### 1. Clone
```bash
git clone https://github.com/aarya-114/contract.git
cd contractsense
```

### 2. Environment
```bash
cp backend/.env.example backend/.env
# Add your GROQ_API_KEY to backend/.env
```

### 3. Run with Docker
```bash
docker-compose up --build
```

### 4. Run locally
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### 5. Open
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

---

## 📊 Risk Scoring
```
Clause types weighted by importance:
  termination, liability, payment,
  intellectual_property, dispute_resolution → 2x weight

Risk levels:
  safe    = 0 points
  caution = 1 point
  risky   = 3 points

Overall score = (weighted_sum / max_possible) × 100

Labels:
  0-20:  Low
  20-40: Medium
  40-65: High
  65+:   Critical
```

---

## ⚠️ Disclaimer

ContractSense provides AI-assisted analysis for informational purposes only. This is not legal advice. Always consult a qualified lawyer before signing any contract.

---

