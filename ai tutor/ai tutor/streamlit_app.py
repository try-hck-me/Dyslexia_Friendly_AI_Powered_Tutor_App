import streamlit as st
import requests
import pandas as pd
import json
import time
import markdown2
import base64
import re

try:
    from streamlit_agraph import agraph, Node, Edge, Config
    AGRAPH_AVAILABLE = True
except ImportError:
    AGRAPH_AVAILABLE = False

# ─── Configuration ───
API_BASE = "http://localhost:8000"
DEFAULT_USER_ID = "tester_123"

st.set_page_config(
    page_title="AI Tutor — Dyslexia-Friendly Learning Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Premium Custom Styles ───
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Lexend:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    /* ═══════════════════════════════════════════════════
       ROOT & GLOBAL
       ═══════════════════════════════════════════════════ */
    
    :root {
        --bg-primary: #0c0e1a;
        --bg-card: rgba(22, 27, 45, 0.85);
        --bg-card-hover: rgba(30, 36, 58, 0.95);
        --border-subtle: rgba(139, 92, 246, 0.15);
        --border-glow: rgba(139, 92, 246, 0.35);
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --accent-purple: #8b5cf6;
        --accent-pink: #ec4899;
        --accent-blue: #6366f1;
        --accent-cyan: #22d3ee;
        --accent-green: #34d399;
        --accent-amber: #fbbf24;
        --gradient-main: linear-gradient(135deg, #8b5cf6, #ec4899);
        --gradient-cool: linear-gradient(135deg, #6366f1, #22d3ee);
        --shadow-glow: 0 0 30px rgba(139, 92, 246, 0.12);
    }

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stApp {
        background: var(--bg-primary);
        background-image: 
            radial-gradient(ellipse at 10% 20%, rgba(139, 92, 246, 0.08), transparent 50%),
            radial-gradient(ellipse at 90% 80%, rgba(236, 72, 153, 0.06), transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(99, 102, 241, 0.04), transparent 60%);
        color: var(--text-primary);
    }

    .main .block-container {
        padding: 2rem 3rem 3rem 3rem;
        max-width: 1100px;
    }

    /* ═══════════════════════════════════════════════════
       SIDEBAR
       ═══════════════════════════════════════════════════ */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 18, 35, 0.97), rgba(20, 24, 42, 0.97)) !important;
        border-right: 1px solid var(--border-subtle) !important;
        backdrop-filter: blur(20px);
    }

    [data-testid="stSidebar"] * {
        color: var(--text-secondary) !important;
    }

    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.15rem;
    }

    [data-testid="stSidebar"] .stRadio label {
        color: var(--text-secondary) !important;
        padding: 0.55rem 0.75rem !important;
        border-radius: 0.6rem !important;
        transition: all 0.25s ease !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        border: 1px solid transparent !important;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(139, 92, 246, 0.12) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-subtle) !important;
    }

    [data-testid="stSidebar"] .stRadio label[data-checked="true"],
    [data-testid="stSidebar"] .stRadio label[aria-checked="true"] {
        background: rgba(139, 92, 246, 0.18) !important;
        color: #e0d4ff !important;
        border-color: var(--border-glow) !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(139, 92, 246, 0.12) !important;
        margin: 0.75rem 0 !important;
    }

    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stTextInput input {
        color: var(--text-secondary) !important;
    }

    [data-testid="stSidebar"] .stTextInput input {
        background: rgba(30, 35, 55, 0.8) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0.6rem !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] .stTextInput input:focus {
        border-color: var(--accent-purple) !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important;
    }

    /* ═══════════════════════════════════════════════════
       TYPOGRAPHY
       ═══════════════════════════════════════════════════ */

    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }

    /* Page Headers */
    .page-header {
        font-size: 2rem;
        font-weight: 800;
        background: var(--gradient-main);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
        line-height: 1.2;
    }

    .page-subtitle {
        color: var(--text-muted);
        font-size: 1.05rem;
        margin-bottom: 2rem;
        font-weight: 400;
        line-height: 1.5;
    }

    /* Sidebar title */
    .sidebar-brand {
        font-size: 1.5rem;
        font-weight: 800;
        background: var(--gradient-main);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
        display: block;
    }

    .sidebar-tagline {
        color: var(--text-muted) !important;
        font-size: 0.82rem;
        font-weight: 500;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        display: block;
        margin-bottom: 0.5rem;
    }

    /* ═══════════════════════════════════════════════════
       CARDS & CONTAINERS
       ═══════════════════════════════════════════════════ */

    .glass-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 1rem;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        box-shadow: var(--shadow-glow);
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-glow);
        box-shadow: 0 0 40px rgba(139, 92, 246, 0.15);
    }

    /* ═══════════════════════════════════════════════════
       METRIC CARDS
       ═══════════════════════════════════════════════════ */

    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
        border-color: var(--border-glow);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: var(--gradient-main);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2;
    }

    .metric-label {
        color: var(--text-muted);
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 0.4rem;
    }

    /* ═══════════════════════════════════════════════════
       CHAT BUBBLES
       ═══════════════════════════════════════════════════ */

    .chat-row { display: flex; margin-bottom: 1rem; }
    .chat-row-user { justify-content: flex-end; }
    .chat-row-bot { justify-content: flex-start; }

    .chat-bubble {
        padding: 1rem 1.25rem;
        border-radius: 1.1rem;
        max-width: 80%;
        font-size: 0.95rem;
        line-height: 1.65;
        color: var(--text-primary);
        word-wrap: break-word;
    }

    .user-bubble {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.22), rgba(99, 102, 241, 0.18));
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-bottom-right-radius: 0.25rem;
    }

    .bot-bubble {
        background: linear-gradient(135deg, #6366f1, #7c3aed);
        color: #ffffff;
        border-bottom-left-radius: 0.25rem;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25);
    }

    .friendly-bubble {
        background: linear-gradient(135deg, #ec4899, #f472b6);
        color: #ffffff;
        border-bottom-left-radius: 0.25rem;
        box-shadow: 0 4px 15px rgba(236, 72, 153, 0.25);
    }

    .mood-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: rgba(139, 92, 246, 0.18);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 2rem;
        color: #c4b5fd;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    /* ═══════════════════════════════════════════════════
       FORM ELEMENTS
       ═══════════════════════════════════════════════════ */

    .stTextInput label, .stTextArea label, .stFileUploader label,
    .stSlider label, .stRadio > label, .stSelectbox label,
    .stNumberInput label {
        color: var(--text-secondary) !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        letter-spacing: 0.01em;
    }

    .stTextInput input, .stTextArea textarea {
        background: rgba(22, 27, 45, 0.9) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0.7rem !important;
        color: var(--text-primary) !important;
        font-size: 0.95rem !important;
        padding: 0.65rem 0.85rem !important;
        transition: all 0.25s ease !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent-purple) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15) !important;
    }

    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
        opacity: 0.7 !important;
    }

    /* ═══════════════════════════════════════════════════
       BUTTONS
       ═══════════════════════════════════════════════════ */

    .stButton > button {
        background: var(--gradient-main) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 0.7rem !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.02em;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 25px rgba(139, 92, 246, 0.4) !important;
        filter: brightness(1.1);
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    .stFormSubmitButton > button {
        background: var(--gradient-main) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 0.7rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
        transition: all 0.3s ease !important;
    }

    .stFormSubmitButton > button:hover {
        box-shadow: 0 6px 25px rgba(139, 92, 246, 0.4) !important;
        filter: brightness(1.1);
    }

    /* ═══════════════════════════════════════════════════
       FILE UPLOADER
       ═══════════════════════════════════════════════════ */

    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 2px dashed var(--border-glow) !important;
        border-radius: 1rem !important;
        padding: 1.5rem !important;
    }

    [data-testid="stFileUploader"] label {
        color: var(--text-secondary) !important;
    }

    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small {
        color: var(--text-muted) !important;
    }

    [data-testid="stFileUploader"] button {
        background: rgba(139, 92, 246, 0.15) !important;
        border: 1px solid var(--border-glow) !important;
        color: var(--text-primary) !important;
        border-radius: 0.6rem !important;
    }

    /* ═══════════════════════════════════════════════════
       ALERTS & STATUS
       ═══════════════════════════════════════════════════ */

    .stAlert {
        border-radius: 0.8rem !important;
        border: none !important;
    }

    /* Success message in sidebar */
    [data-testid="stSidebar"] [data-testid="stAlert"] {
        background: rgba(52, 211, 153, 0.12) !important;
        border: 1px solid rgba(52, 211, 153, 0.3) !important;
        border-radius: 0.6rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stAlert"] p {
        color: var(--accent-green) !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
    }

    /* Error message in sidebar */
    [data-testid="stSidebar"] .stAlert[data-baseweb="notification"] {
        border-radius: 0.6rem !important;
    }

    /* ═══════════════════════════════════════════════════
       METRICS (Streamlit native)
       ═══════════════════════════════════════════════════ */

    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 1rem !important;
        padding: 1.25rem !important;
        text-align: center;
        transition: all 0.3s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: var(--border-glow) !important;
        box-shadow: var(--shadow-glow);
    }

    [data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }

    /* ═══════════════════════════════════════════════════
       DATAFRAME / TABLE
       ═══════════════════════════════════════════════════ */

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0.8rem !important;
        overflow: hidden;
    }

    /* ═══════════════════════════════════════════════════
       EXPANDER
       ═══════════════════════════════════════════════════ */

    [data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0.8rem !important;
        margin-bottom: 0.5rem;
    }

    [data-testid="stExpander"] summary {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    [data-testid="stExpander"] p,
    [data-testid="stExpander"] span {
        color: var(--text-secondary) !important;
    }

    /* ═══════════════════════════════════════════════════
       SLIDER
       ═══════════════════════════════════════════════════ */

    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"] {
        color: var(--text-muted) !important;
    }

    .stSlider p {
        color: var(--text-secondary) !important;
    }

    /* ═══════════════════════════════════════════════════
       DIVIDER
       ═══════════════════════════════════════════════════ */

    hr {
        border-color: rgba(139, 92, 246, 0.1) !important;
    }

    /* ═══════════════════════════════════════════════════
       RADIO (Quiz options)
       ═══════════════════════════════════════════════════ */

    .stRadio label {
        color: var(--text-secondary) !important;
    }

    /* ═══════════════════════════════════════════════════
       INFO / WARNING / SUCCESS / ERROR Boxes (main area)
       ═══════════════════════════════════════════════════ */

    [data-testid="stAlert"] p {
        color: inherit !important;
        font-weight: 500 !important;
    }

    /* ═══════════════════════════════════════════════════
       CAPTIONS / SMALL TEXT
       ═══════════════════════════════════════════════════ */

    .stCaption, caption, .stMarkdown small {
        color: var(--text-muted) !important;
    }

    /* Paragraph text */
    .stMarkdown p {
        color: var(--text-secondary);
    }

    /* ═══════════════════════════════════════════════════
       SECTION HEADER (used in Analytics, etc.)
       ═══════════════════════════════════════════════════ */

    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(139, 92, 246, 0.2);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ═══════════════════════════════════════════════════
       SCROLLBAR
       ═══════════════════════════════════════════════════ */

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(139, 92, 246, 0.5); }

    /* ═══════════════════════════════════════════════════
       CHART CONTAINER
       ═══════════════════════════════════════════════════ */

    [data-testid="stVegaLiteChart"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 0.8rem !important;
        padding: 1rem !important;
    }

    /* ═══════════════════════════════════════════════════
       RECOMMENDATION CARD
       ═══════════════════════════════════════════════════ */

    .rec-item {
        padding: 0.75rem 1rem;
        background: rgba(139, 92, 246, 0.08);
        border-left: 3px solid var(--accent-purple);
        border-radius: 0 0.5rem 0.5rem 0;
        margin-bottom: 0.5rem;
        color: var(--text-secondary);
        font-size: 0.92rem;
        line-height: 1.5;
    }

    /* ═══════════════════════════════════════════════════
       QUIZ QUESTION CARD
       ═══════════════════════════════════════════════════ */

    .quiz-q {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
    }

    .quiz-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.2rem 0.65rem;
        border-radius: 2rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge-easy {
        background: rgba(52, 211, 153, 0.15);
        color: var(--accent-green);
        border: 1px solid rgba(52, 211, 153, 0.3);
    }

    .badge-medium {
        background: rgba(251, 191, 36, 0.15);
        color: var(--accent-amber);
        border: 1px solid rgba(251, 191, 36, 0.3);
    }

    .badge-hard {
        background: rgba(236, 72, 153, 0.15);
        color: var(--accent-pink);
        border: 1px solid rgba(236, 72, 153, 0.3);
    }

    /* ═══════════════════════════════════════════════════
       EMPTY STATE
       ═══════════════════════════════════════════════════ */

    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        color: var(--text-muted);
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.6;
    }

    .empty-state-text {
        font-size: 1rem;
        color: var(--text-muted);
        max-width: 400px;
        margin: 0 auto;
        line-height: 1.6;
    }

</style>
""", unsafe_allow_html=True)
# ─── State Initialization ───
if "user_id" not in st.session_state:
    st.session_state.user_id = DEFAULT_USER_ID

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "friendly_history" not in st.session_state:
    st.session_state.friendly_history = []

if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
    st.session_state.current_quiz = None
    st.session_state.quiz_topic = ""
    st.session_state.user_answers = {}

if "dyslexia_mode" not in st.session_state:
    st.session_state.dyslexia_mode = False
if "font_size" not in st.session_state:
    st.session_state.font_size = 1.0
if "line_spacing" not in st.session_state:
    st.session_state.line_spacing = 1.65
if "char_spacing" not in st.session_state:
    st.session_state.char_spacing = 0.0
if "tts_voice" not in st.session_state:
    st.session_state.tts_voice = "shubh"

# ─── Dynamic Dyslexia Styles ───
if st.session_state.dyslexia_mode:
    st.markdown(f"""
    <style>
        * {{
            font-family: 'Lexend', sans-serif !important;
            letter-spacing: {st.session_state.char_spacing}px !important;
            word-spacing: {st.session_state.char_spacing * 2}px !important;
        }}
        .chat-bubble, .stMarkdown p, .stMarkdown li {{
            font-size: {st.session_state.font_size}rem !important;
            line-height: {st.session_state.line_spacing} !important;
        }}
        .bot-bubble, .friendly-bubble {{
            background: #ffffff !important;
            color: #1e293b !important;
            border: 2px solid #8b5cf6 !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        }}
        .user-bubble {{
            background: #f1f5f9 !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }}
        /* Ensure lists look right */
        .chat-bubble ul, .chat-bubble ol {{
            margin-left: 1.5rem !important;
            margin-bottom: 1rem !important;
        }}
        .chat-bubble li {{
            margin-bottom: 0.5rem !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# ─── TTS Helpers ───
def clean_for_tts(text: str) -> str:
    text = re.sub(r'[*_#`~]', '', text) 
    text = re.sub(r'\[.*?\]\(.*?\)', '', text) 
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def render_tts_button(text_to_read: str, unique_key: str):
    """Renders a 'Read Aloud' button and audio player using Sarvam AI."""
    session_key = f"audio_{unique_key}"
    play_key = f"play_{unique_key}"
    
    col1, col2 = st.columns([1.5, 8.5])
    with col1:
        if st.button("🔊 Read", key=f"btn_{unique_key}", help="Read this aloud"):
            st.session_state[play_key] = True

    if st.session_state.get(play_key):
        if session_key not in st.session_state:
            with st.spinner("Loading audio..."):
                try:
                    safe_text = clean_for_tts(text_to_read)[:2490]
                    payload = {
                        "text": safe_text,
                        "speaker": st.session_state.get("tts_voice", "shubh")
                    }
                    res = requests.post(f"{API_BASE}/tts", json=payload)
                    if res.status_code == 200:
                        b64 = res.json()["data"]["audio"]
                        st.session_state[session_key] = base64.b64decode(b64)
                    else:
                        st.error("Audio generation failed.")
                        st.session_state[play_key] = False
                except Exception as e:
                    st.error("TTS connection error.")
                    st.session_state[play_key] = False
                    
        if st.session_state.get(session_key):
            st.audio(st.session_state[session_key], format="audio/wav", autoplay=True)
            st.session_state[play_key] = False

# ─── Sidebar Navigation ───
with st.sidebar:
    st.markdown('<span class="sidebar-brand">AI Tutor ✨</span>', unsafe_allow_html=True)
    st.markdown('<span class="sidebar-tagline">Dyslexia-Friendly Learning</span>', unsafe_allow_html=True)
    st.divider()
    
    selection = st.radio(
        "Navigation",
        ["📄 Study Material", "🤖 Study Bot", "🕸️ Knowledge Graph", "❤️ FriendlyBot", "🧠 Quiz Generator", "📊 Analytics"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id)
    
    st.markdown("---")
    st.markdown('<span class="sidebar-tagline">🧠 Dyslexia Support</span>', unsafe_allow_html=True)
    st.session_state.dyslexia_mode = st.toggle("Dyslexia-Friendly Mode", value=st.session_state.dyslexia_mode)
    
    if st.session_state.dyslexia_mode:
        st.session_state.font_size = st.slider("Font Size (rem)", 0.8, 1.5, st.session_state.font_size)
        st.session_state.line_spacing = st.slider("Line Spacing", 1.2, 2.5, st.session_state.line_spacing)
        st.session_state.char_spacing = st.slider("Letter Spacing (px)", 0, 5, int(st.session_state.char_spacing * 10)) / 10.0
    
    st.markdown("---")
    st.markdown('<span class="sidebar-tagline">🔊 Read Aloud Voice</span>', unsafe_allow_html=True)
    
    # Pre-select matching option from session state if available
    tts_options = ["shubh (Male)", "aditya (Male)", "ritu (Female)", "priya (Female)", "kavya (Female)"]
    default_idx = 0
    for i, opt in enumerate(tts_options):
        if opt.startswith(st.session_state.tts_voice):
            default_idx = i
            break
            
    selected_voice = st.selectbox("Select Voice", tts_options, index=default_idx, label_visibility="collapsed")
    st.session_state.tts_voice = selected_voice.split(" ")[0]
    
    st.markdown("---")
    try:
        health = requests.get(API_BASE, timeout=2).json()
        st.success(f"✅ API Online (v{health.get('version')})")
    except Exception:
        st.error("⚠️ API Offline — Run uvicorn server!")

# ═══════════════════════════════════════════════════════════
# MODULE: 📄 Study Material
# ═══════════════════════════════════════════════════════════
if selection == "📄 Study Material":
    st.markdown('<div class="page-header">📄 Upload Study Material</div>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Upload your textbook or notes as a PDF. We\'ll extract the text, split it into smart chunks, and store it in your personal knowledge base for instant retrieval.</p>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload a textbook or notes (PDF)", type="pdf")
    
    if uploaded_file is not None:
        if st.button("🚀 Process & Store", use_container_width=True):
            with st.spinner("Analyzing and embedding document..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                try:
                    res = requests.post(f"{API_BASE}/upload", files=files)
                    data = res.json()
                    
                    if data.get("success"):
                        filename = uploaded_file.name
                        progress_bar = st.progress(0, text="Starting...")
                        status_text = st.empty()
                        
                        # Polling loop
                        completed = False
                        while not completed:
                            time.sleep(1)
                            try:
                                status_res = requests.get(f"{API_BASE}/upload/status/{filename}")
                                status_data = status_res.json()
                                
                                if status_data.get("success"):
                                    p_info = status_data["data"]
                                    progress = p_info["progress"] / 100.0
                                    status = p_info["status"]
                                    completed = p_info.get("completed", False)
                                    err = p_info.get("error")
                                    
                                    progress_bar.progress(progress, text=status)
                                    status_text.markdown(f"**Status:** {status}")
                                    
                                    if err:
                                        st.error(f"Processing error: {err}")
                                        break
                                else:
                                    st.error("Failed to fetch processing status.")
                                    break
                            except Exception as e:
                                st.error(f"Status polling error: {e}")
                                break
                        
                        if completed:
                            st.success(f"✅ Processing complete for '{filename}'!")
                            # Optional: refresh list or show details
                            # Original behavior was to show data from upload response
                            # but now the real data is in the status or final step.
                    else:
                        st.error(f"Error: {data.get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Connection error: {e}")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📂</div>
            <div class="empty-state-text">Drag and drop a PDF above, or click <strong>Browse files</strong> to get started.</div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# MODULE: 🤖 Study Bot
# ═══════════════════════════════════════════════════════════
elif selection == "🤖 Study Bot":
    st.markdown('<div class="page-header">🤖 Study Bot</div>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Ask questions about your uploaded PDFs — get clear, simple answers powered by RAG.</p>', unsafe_allow_html=True)
    
    # Display Chat History
    chat_container = st.container()
    with chat_container:
        if st.session_state.chat_history:
            for i, chat in enumerate(st.session_state.chat_history):
                user_html = markdown2.markdown(chat["q"])
                bot_html = markdown2.markdown(chat["a"])
                st.markdown(f'<div class="chat-row chat-row-user"><div class="chat-bubble user-bubble">{user_html}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="chat-row chat-row-bot"><div class="chat-bubble bot-bubble">{bot_html}</div></div>', unsafe_allow_html=True)
                
                if chat["a"] != "Thinking...":
                    render_tts_button(chat["a"], f"studybot_{i}")
                
                if chat.get("sources"):
                    st.caption(f"📚 Sources: {', '.join(chat['sources'])}")
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <div class="empty-state-text">No messages yet. Ask a question about your study material below!</div>
            </div>
            """, unsafe_allow_html=True)

    # Input Area
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([8, 1])
        question = col1.text_input("Your question", placeholder="E.g., What is photosynthesis?", label_visibility="collapsed")
        submitted = col2.form_submit_button("Ask ✨")
        
        if submitted and question:
            st.session_state.chat_history.append({"q": question, "a": "Thinking..."})
            
            with st.spinner("Searching your knowledge base..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/chat",
                        json={"user_id": st.session_state.user_id, "question": question}
                    )
                    data = res.json()
                    
                    if data.get("success"):
                        ans = data["data"]["answer"]
                        sources = list(set([s["source"] for s in data["data"].get("sources", [])]))
                        
                        st.session_state.chat_history[-1]["a"] = ans
                        st.session_state.chat_history[-1]["sources"] = sources
                        st.rerun()
                    else:
                        st.error(data.get("detail", "Error"))
                except Exception as e:
                    st.error(f"Failed to connect: {e}")

# ═══════════════════════════════════════════════════════════
# MODULE: 🕸️ Knowledge Graph
# ═══════════════════════════════════════════════════════════
elif selection == "🕸️ Knowledge Graph":
    st.markdown('<div class="page-header">🕸️ Knowledge Graph</div>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Visualize the concepts, relationships, and structure extracted from your notes as an interactive graph.</p>', unsafe_allow_html=True)

    if not AGRAPH_AVAILABLE:
        st.warning("⚠️ The `streamlit-agraph` package is not installed. Install it with: `pip install streamlit-agraph`")
    else:
        with st.spinner("Fetching graph data..."):
            try:
                res = requests.get(f"{API_BASE}/graph/viz")
                data = res.json()
                if data.get("success") and data["data"]["nodes"]:
                    node_count = data['data']['count']['nodes']
                    edge_count = data['data']['count']['edges']
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Nodes", node_count)
                    col2.metric("Edges", edge_count)
                    
                    nodes = [
                        Node(
                            id=n["id"],
                            label=n["label"],
                            size=n["size"],
                            color=n["color"],
                            title=n["title"]
                        )
                        for n in data["data"]["nodes"]
                    ]
                    
                    edges = [
                        Edge(
                            source=e["source"],
                            target=e["target"],
                            label=e["label"],
                            color=e["color"]
                        )
                        for e in data["data"]["edges"]
                    ]

                    config = Config(
                        width="100%",
                        height=600,
                        directed=True,
                        physics=True,
                        hierarchical=False,
                    )

                    agraph(nodes=nodes, edges=edges, config=config)
                    
                else:
                    st.markdown("""
                    <div class="empty-state">
                        <div class="empty-state-icon">🕸️</div>
                        <div class="empty-state-text">No knowledge graph available yet. Upload a PDF first to build your graph!</div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to fetch graph visualization: {e}")

# ═══════════════════════════════════════════════════════════
# MODULE: ❤️ FriendlyBot
# ═══════════════════════════════════════════════════════════
elif selection == "❤️ FriendlyBot":
    st.markdown('<div class="page-header">❤️ FriendlyBot</div>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">How are you feeling today? Share your thoughts — I\'m here to listen and support you.</p>', unsafe_allow_html=True)
    
    # History
    if st.session_state.friendly_history:
        for i, chat in enumerate(st.session_state.friendly_history):
            user_html = markdown2.markdown(chat["msg"])
            bot_html = markdown2.markdown(chat["res"])
            st.markdown(f'<div class="chat-row chat-row-user"><div class="chat-bubble user-bubble">{user_html}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<span class="mood-badge">Mood: {chat["mood"]}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-row chat-row-bot"><div class="chat-bubble friendly-bubble">{bot_html}</div></div>', unsafe_allow_html=True)
            
            render_tts_button(chat["res"], f"friendlybot_{i}")
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">💝</div>
            <div class="empty-state-text">No conversations yet. Tell me how you're feeling — I'm here to help and encourage you!</div>
        </div>
        """, unsafe_allow_html=True)

    with st.form("friendly_form", clear_on_submit=True):
        msg = st.text_input("Your message", placeholder="I'm feeling a bit stressed about my exams...")
        sent = st.form_submit_button("Share ❤️")
        
        if sent and msg:
            with st.spinner("Listening..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/friendly",
                        json={"user_id": st.session_state.user_id, "message": msg}
                    )
                    data = res.json()
                    if data.get("success"):
                        st.session_state.friendly_history.append({
                            "msg": msg,
                            "mood": data["data"]["mood"],
                            "res": data["data"]["response"]
                        })
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════
# MODULE: 🧠 Quiz Generator
# ═══════════════════════════════════════════════════════════
elif selection == "🧠 Quiz Generator":
    st.markdown('<div class="page-header">🧠 Adaptive Quiz</div>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Generate MCQs that adapt to your knowledge level. The difficulty adjusts based on your past performance.</p>', unsafe_allow_html=True)
    
    if not st.session_state.quiz_active:
        topic = st.text_input("📝 Quiz Topic", placeholder="E.g., Cells, Mitosis, Photosynthesis")
        num = st.slider("Number of Questions", 1, 10, 5)
        
        if st.button("🎯 Generate Quiz", use_container_width=True):
            if not topic:
                st.warning("Please enter a topic!")
            else:
                with st.spinner("Generating adaptive questions..."):
                    try:
                        res = requests.post(
                            f"{API_BASE}/quiz",
                            json={"user_id": st.session_state.user_id, "topic": topic, "num_questions": num}
                        )
                        data = res.json()
                        if data.get("success"):
                            st.session_state.current_quiz = data["data"]
                            st.session_state.quiz_active = True
                            st.session_state.quiz_topic = topic
                            st.session_state.user_answers = {}
                            st.rerun()
                        else:
                            st.error(data.get("error", "Generation failed"))
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        q_data = st.session_state.current_quiz
        difficulty = q_data['difficulty'].lower()
        badge_class = f"badge-{difficulty}" if difficulty in ['easy', 'medium', 'hard'] else 'badge-medium'
        
        st.markdown(f"""
        <div class="glass-card" style="display:flex; align-items:center; justify-content:space-between; padding:1rem 1.5rem;">
            <span style="color:var(--text-primary); font-weight:600;">Topic: {q_data['topic']}</span>
            <span class="quiz-badge {badge_class}">{q_data['difficulty']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        for i, q in enumerate(q_data["questions"]):
            st.markdown(f'<div class="quiz-q">{i+1}. {q["question"]}</div>', unsafe_allow_html=True)
            
            # Read Question and Options aloud
            tts_text = f"Question {i+1}. {q['question']} Options are: " + ". ".join(q["options"])
            render_tts_button(tts_text, f"quiz_{st.session_state.quiz_topic}_{i}")
            
            choice = st.radio(f"Select answer for question {i+1}", q["options"], key=f"q_{i}", label_visibility="collapsed")
            st.session_state.user_answers[i] = choice
            st.divider()
            
        col_submit, col_cancel = st.columns([3, 1])
        
        with col_submit:
            if st.button("📤 Submit Quiz", use_container_width=True):
                with st.spinner("Scoring..."):
                    payload = {
                        "user_id": st.session_state.user_id,
                        "topic": q_data["topic"],
                        "questions": q_data["questions"],
                        "answers": [{"question_index": i, "selected": ans} for i, ans in st.session_state.user_answers.items()]
                    }
                    try:
                        res = requests.post(f"{API_BASE}/quiz/submit", json=payload)
                        data = res.json()
                        if data.get("success"):
                            st.session_state.quiz_active = False
                            st.balloons()
                            score = data['data']['score']
                            total = data['data']['total']
                            pct = data['data']['percentage']
                            st.success(f"🎉 Final Score: {score}/{total} ({pct}%)")
                            
                            for r in data["data"]["results"]:
                                icon = "✅" if r['is_correct'] else "❌"
                                with st.expander(f"{icon} Question {r['question_index']+1}"):
                                    st.markdown(f"**Your answer:** {r['selected']}")
                                    st.markdown(f"**Correct answer:** {r['correct']}")
                                    st.markdown(f"**Explanation:** {r['explanation']}")
                        else:
                            st.error("Submission failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.quiz_active = False
                st.rerun()

# ═══════════════════════════════════════════════════════════
# MODULE: 📊 Analytics
# ═══════════════════════════════════════════════════════════
elif selection == "📊 Analytics":
    st.markdown('<div class="page-header">📊 Your Analytics</div>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Track your study progress, topic mastery, and emotional well-being over time.</p>', unsafe_allow_html=True)
    
    try:
        res = requests.get(f"{API_BASE}/analytics/{st.session_state.user_id}")
        data = res.json()
        
        if data.get("success"):
            stats = data["data"]
            
            # Key Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Questions Asked", stats["study_stats"]["questions_asked"])
            m2.metric("Quizzes Taken", stats["study_stats"]["quizzes_taken"])
            m3.metric("Avg Score", f"{stats['study_stats']['avg_quiz_score']}%")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Mood Trends + Recommendations
            col_l, col_r = st.columns(2)
            
            with col_l:
                st.markdown('<div class="section-header">❤️ Mood Trends</div>', unsafe_allow_html=True)
                mood_counts = stats["mood_trends"]["counts"]
                mood_df = pd.DataFrame(list(mood_counts.items()), columns=["Mood", "Count"])
                st.bar_chart(mood_df.set_index("Mood"))
                dominant = stats['mood_trends']['dominant_mood']
                st.markdown(f'<div class="mood-badge" style="margin-top:0.5rem">Dominant: {dominant.upper()}</div>', unsafe_allow_html=True)
                
            with col_r:
                st.markdown('<div class="section-header">💡 AI Recommendations</div>', unsafe_allow_html=True)
                recs = stats["recommendations"]
                if recs:
                    for rec in recs:
                        st.markdown(f'<div class="rec-item">{rec}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="rec-item">Keep studying and taking quizzes to get personalized recommendations!</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Weak Topics
            st.markdown('<div class="section-header">⚠️ Topic Performance</div>', unsafe_allow_html=True)
            if stats["weak_topics"]:
                weak_df = pd.DataFrame(stats["weak_topics"])
                st.dataframe(weak_df, use_container_width=True)
            else:
                st.success("🌟 No weak topics found! You're doing great across all areas.")
                
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-text">No analytics data yet. Start chatting with the Study Bot or take some quizzes to see your progress here!</div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Could not load analytics: {e}")
