# 🧠 AI Tutor & Dyslexia-Friendly Learning Assistant

Welcome to the **AI Tutor & Dyslexia-Friendly Learning Assistant** repository. This is a comprehensive, production-ready educational platform designed as a **Bachelor of Technology Project (BTP 2026)** to assist students with dyslexia in learning more effectively.

The project is split into two main layers:
1. **Next.js Frontend (`/dyslexia-app`)**: A web interface tailored for accessibility, offering adjustable typography (Lexend, OpenDyslexic), contrast settings, Text-to-Speech (TTS), voice input, and clean visual layouts.
2. **FastAPI & Streamlit Backend (`/ai tutor/ai tutor`)**: A Python-based intelligence engine providing a Retrieval-Augmented Generation (RAG) study bot, an adaptive quiz generator, an emotional support chatbot (FriendlyBot) with sentiment analysis, and a detailed student progress analytics engine.

---

## 🗺️ Repository Structure

```text
End Sem/
├── dyslexia-app/               # Next.js frontend web application
│   ├── src/
│   │   ├── app/                # App router (login, dashboard, chat, quiz, reader, analytics, etc.)
│   │   ├── components/         # Reusable UI elements
│   │   ├── context/            # React state context
│   │   └── lib/                # Client utility libraries
│   ├── package.json            # Node.js dependencies (Next.js 16, React 19, react-pdf, etc.)
│   └── README.md               # Frontend template documentation
│
└── ai tutor/
    └── ai tutor/               # Python backend engine
        ├── app/                # FastAPI modules (main, api routing, DB models, RAG/AI services)
        ├── sample_data/        # Sample educational PDFs
        ├── streamlit_app.py    # Streamlit dashboard interface for teachers/parents/admins
        ├── requirements.txt    # Python dependencies (FastAPI, Groq, ChromaDB, etc.)
        └── README.md           # Detailed backend API documentation
```

---

## ✨ Features & Functionality

| Module | Purpose / Feature | Tech Applied |
| :--- | :--- | :--- |
| **📄 RAG Chatbot** | Upload study PDFs and ask questions. Outputs responses in bulleted, simple, dyslexia-friendly language instead of large text blocks. | FastAPI + PyMuPDF + Sentence Transformers + ChromaDB + Groq API (Llama 3) |
| **❤️ FriendlyBot** | Emotional support bot that checks on user stress, detects mood/frustration, and provides positive reinforcement. | TextBlob sentiment analysis + LLM fallback |
| **🧠 Adaptive Quiz** | Generates MCQs dynamically from notes. Adapts difficulty (easy, medium, hard) on the fly based on user performance. | Adaptive quiz engine + SQLite database |
| **📊 Analytics Engine** | Displays performance trends, flags weak topics, graphs dominant moods, and delivers tailored suggestions. | SQLite + SQLAlchemy + Chart.js |
| **👓 Accessibility App** | Responsive frontend UI featuring OpenDyslexic & Atkinson Hyperlegible fonts, customizable font-size, letter-spacing, page theme/contrast, and Text-to-Speech (TTS). | Next.js + React + `@fontsource` accessibility packages |

---

## 🛠️ Tech Stack

### Frontend (`/dyslexia-app`)
- **Framework**: Next.js 16.2.4 (React 19.2.4)
- **Styling**: Vanilla CSS with support for dark/high-contrast accessibility themes
- **Icons**: Lucide React
- **Visualization**: Chart.js & React Chartjs 2 (for student analytics graphs)
- **PDF Viewer**: React-PDF & PDF.js
- **Fonts**: Atkinson Hyperlegible, Lexend, and OpenDyslexic

### Backend (`/ai tutor/ai tutor`)
- **API Framework**: FastAPI (Python 3.10+)
- **LLM Engine**: Groq Cloud API (Llama 3 70B model)
- **Vector Database**: ChromaDB (for storing indexed PDF document chunks)
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`) running locally
- **Database**: SQLite (via SQLAlchemy ORM)
- **Sentiment Analysis**: TextBlob + LLM fallback
- **Dashboard**: Streamlit (useful for quick admin/teacher/parent visualizations)

---

## ⚡ Architecture Flow

```text
               +-------------------------------------------+
               |           Next.js Frontend                |
               | (Accessibility UI, Custom Fonts, TTS/STT) |
               +--------------------+----------------------+
                                    | HTTP Requests (JSON / Multipart)
                                    v
                       +------------+------------+
                       |     FastAPI Backend     |
                       +------------+------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
     [ ChromaDB Vector ]     [ SQLite database ]     [ Groq Cloud LLM ]
    - Document chunks       - User accounts         - RAG generation
    - Note embeddings       - Quiz results          - FriendlyBot responses
                            - Mood history          - MCQ Generation
```

---

## 🚀 Setup & Installation

### 1. Backend Setup (`ai tutor/ai tutor`)

Navigate to the nested backend directory:
```bash
cd "ai tutor/ai tutor"
```

#### Step A: Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step B: Install Python Packages
```bash
pip install -r requirements.txt
```

#### Step C: Configure Environments
Create a `.env` file in `ai tutor/ai tutor/` and supply your Groq API Key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```
> Get your key from the [Groq Console](https://console.groq.com/keys).

#### Step D: Run the FastAPI Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs will be available at: `http://localhost:8000/docs`
- Redoc will be available at: `http://localhost:8000/redoc`

#### Step E: (Optional) Run the Streamlit Admin/Tutor Dashboard
In a separate terminal (with your virtual env active):
```bash
streamlit run streamlit_app.py
```
- Streamlit application will launch at: `http://localhost:8501`

---

### 2. Frontend Setup (`dyslexia-app`)

Open a new terminal window and navigate to the frontend directory:
```bash
cd dyslexia-app
```

#### Step A: Install Node Dependencies
```bash
npm install
```

#### Step B: Run Development Server
```bash
npm run dev
```
- The frontend will open at: `http://localhost:3000`

---

## 📄 License & Credits
Developed as part of the **BTP (Bachelor of Technology Project) 2026**.
Released under the MIT License.
