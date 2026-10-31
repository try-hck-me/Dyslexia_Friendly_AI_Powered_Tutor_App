# 🧠 AI Tutor — Dyslexia-Friendly Learning Assistant

A production-ready backend AI system designed to help students with dyslexia learn more effectively. Built with FastAPI, Groq LLM, ChromaDB, and Sentence Transformers.

## ✨ Features

| Module | Description |
|--------|-------------|
| **📄 RAG Chatbot** | Upload PDFs and ask questions — answers in simple, dyslexia-friendly English |
| **❤️ FriendlyBot** | Emotional support AI with mood detection and encouraging responses |
| **🧠 Quiz Generator** | Adaptive MCQs that get harder or easier based on your scores |
| **📊 Analytics Engine** | Track weak topics, mood trends, and get personalized recommendations |

## 🛠️ Tech Stack

- **API Framework:** FastAPI
- **LLM:** Groq API (Llama 3 70B)
- **Vector DB:** ChromaDB
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **PDF Parsing:** PyMuPDF
- **Database:** SQLite (via SQLAlchemy)
- **Sentiment:** TextBlob + LLM fallback

## 🚀 Setup

### 1. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Groq API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get your key at: https://console.groq.com/keys

### 4. Generate sample PDF (optional)

```bash
python create_sample_pdf.py
```

### 5. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

Interactive docs at: `http://localhost:8000/docs`

### 6. Run the Streamlit Frontend

In a new terminal window:

```bash
streamlit run streamlit_app.py
```

The dashboard will open at: `http://localhost:8501`

---

## 📡 API Endpoints

### 1. Upload PDF

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@sample_data/biology_cells.pdf"
```

**Response:**
```json
{
  "success": true,
  "message": "PDF 'biology_cells.pdf' processed successfully.",
  "data": {
    "filename": "biology_cells.pdf",
    "chunks_created": 8,
    "total_documents": 8,
    "text_length": 4521
  }
}
```

### 2. Chat (RAG Chatbot)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "question": "What is a cell?"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "answer": "• A cell is the smallest unit of life.\n• All living things are made of cells.\n• Some have one cell (unicellular), others have many (multicellular).",
    "sources": [...],
    "context_found": true
  }
}
```

### 3. FriendlyBot (Emotional Support)

```bash
curl -X POST http://localhost:8000/friendly \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "message": "I feel stressed about my exams"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "mood": "stressed",
    "response": "Hey, it's okay to feel this way! 💙 Exams can be tough, but remember you've been working hard. Take a 5-minute break, breathe deeply, and come back refreshed. You've got this! 🌟"
  }
}
```

### 4. Generate Quiz

```bash
curl -X POST http://localhost:8000/quiz \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "topic": "cells"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "question": "What is the smallest unit of life?",
        "options": ["Atom", "Cell", "Tissue", "Organ"],
        "answer": "Cell",
        "explanation": "A cell is the smallest unit of life. All living things are made of cells."
      }
    ],
    "difficulty": "medium",
    "topic": "cells",
    "num_questions": 5
  }
}
```

### 5. Submit Quiz

```bash
curl -X POST http://localhost:8000/quiz/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "1",
    "topic": "cells",
    "questions": [{"question": "What is the smallest unit of life?", "options": ["Atom", "Cell", "Tissue", "Organ"], "answer": "Cell", "explanation": "A cell is the smallest unit of life."}],
    "answers": [{"question_index": 0, "selected": "Cell"}]
  }'
```

### 6. Get Analytics

```bash
curl http://localhost:8000/analytics/1
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "1",
    "study_stats": {
      "questions_asked": 5,
      "quizzes_taken": 3,
      "avg_quiz_score": 73.3
    },
    "weak_topics": [
      {"topic": "mitosis", "avg_score": 40.0, "attempts": 2}
    ],
    "mood_trends": {
      "counts": {"happy": 3, "neutral": 5, "stressed": 2, "frustrated": 0},
      "dominant_mood": "neutral"
    },
    "recommendations": [
      "📚 Your score in 'mitosis' is 40.0%. Try revising this topic.",
      "🌟 Great job! Your average score is above 80%. Keep it up!"
    ]
  }
}
```

---

## 📁 Project Structure

```
ai tutor/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── api/
│   │   ├── upload.py           # PDF upload endpoint
│   │   ├── chatbot.py          # RAG chatbot endpoint
│   │   ├── friendlybot.py      # Emotional AI endpoint
│   │   ├── quiz.py             # Quiz generation & submission
│   │   └── analytics.py        # Analytics endpoint
│   ├── services/
│   │   ├── pdf_loader.py       # PDF text extraction
│   │   ├── chunker.py          # Text chunking
│   │   ├── embedding.py        # Sentence Transformers
│   │   ├── vector_store.py     # ChromaDB operations
│   │   ├── retriever.py        # Chunk retrieval
│   │   ├── llm_groq.py         # Groq API client
│   │   ├── rag_pipeline.py     # RAG orchestration
│   │   ├── sentiment.py        # Mood detection
│   │   ├── quiz_generator.py   # Adaptive quiz creation
│   │   └── analytics_engine.py # Analytics & recommendations
│   ├── database/
│   │   ├── db.py               # SQLAlchemy engine
│   │   └── models.py           # ORM models
│   └── utils/
│       ├── prompts.py          # Prompt templates
│       └── formatter.py        # Response formatters
├── data/                       # Auto-created: DB + ChromaDB
├── sample_data/                # Sample PDFs
├── create_sample_pdf.py        # PDF generator script
├── requirements.txt
├── .env.example
└── README.md
```

## 🧪 Architecture

```
PDF Upload → Text Extraction → Chunking → Embeddings → ChromaDB
                                                          ↓
User Question → Embed Query → Vector Search → Top-4 Chunks
                                                          ↓
                              Groq LLM ← Dyslexia-Friendly Prompt
                                                          ↓
                                                    Answer to User
```

## ⚡ Performance Notes

- **Embedding Model**: Loaded once as singleton, reused across requests
- **ChromaDB**: Persistent storage, survives server restarts
- **Batch Embeddings**: Chunks are embedded in batch during upload
- **Low Temperature**: RAG uses temp=0.3 for factual accuracy

## 📄 License

MIT
