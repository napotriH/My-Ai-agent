import streamlit as st
import requests
import json
import re
import sqlite3
import os
from datetime import datetime

# --- CONFIGURARE BRANDING ---
APP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/1698/1698535.png"
APP_NAME = "AI Agent Pro"

# --- API & MODELE ---
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("Lipsește OPENROUTER_API_KEY în Secrets! Te rog adaugă cheia în setările Streamlit Cloud.")
    st.stop()

MODELS = {
    "Kat Coder Pro": "kwaipilot/kat-coder-pro:free",
    "DeepSeek R1": "tngtech/deepseek-r1:free",
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct:free",
    "Mimo V2 Flash": "xiaomi/mimo-v2-flash:free"
}

# --- BAZĂ DE DATE (SQLite) ---
DB_FILE = "agent_storage.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        # Tabel pentru memorie cheie-valoare
        c.execute('''CREATE TABLE IF NOT EXISTS memory 
                     (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)''')
        # Tabel pentru notițe rapide
        c.execute('''CREATE TABLE IF NOT EXISTS notes 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, timestamp TEXT)''')
        conn.commit()

def save_memory(key, value):
    with get_all_db_data() as (mem, _):
        with get_db_connection() as conn:
            c = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT OR REPLACE INTO memory (key, value, updated_at) VALUES (?, ?, ?)", (key, value, now))
            conn.commit()

def add_note(content):
    with get_db_connection() as conn:
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO notes (content, timestamp) VALUES (?, ?)", (content, now))
        conn.commit()

def get_all_db_data():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT key, value FROM memory")
        mem = {row[0]: row[1] for row in c.fetchall()}
        c.execute("SELECT content FROM notes ORDER BY id DESC")
        notes = [row[0] for row in c.fetchall()]
        return mem, notes

init_db()

# --- LOGICĂ AI ---
def ask_ai(prompt, model_url):
    mem, notes = get_all_db_data()
    
    system_message = (
        "Ești un Agent AI Avansat. Ai acces la o bază de date SQLite pentru memorie.\n"
        f"Memorie curentă (JSON): {json.dumps(mem)}\n"
        f"Notițe recente: {', '.join(notes[:5])}\n\n"
        "Comenzi disponibile:\n"
        "- Pentru memorare: :::MEMORIZE:cheie:valoare:::\n"
        "- Pentru notițe: :::NOTE:text:::\n"
        "Răspunde direct și execută comenzile dacă este necesar."
    )

    messages = [{"role": "system", "content": system_message}]
    # Păstrăm ultimele 10 mesaje din sesiune pentru context scurt
    for m in st.session_state.messages[-10:]:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://streamlit.io"
            },
            json={"model": model_url, "messages": messages},
            timeout=45
        )
        response.raise_for_status()
        text = response.json()['choices'][0]['message']['content']
        
        # Procesare comenzi primite de la AI
        if ":::MEMORIZE:" in text:
            match = re.search(r":::MEMORIZE:(.*?):(.*?):::", text)
            if match:
                save_memory(match.group(1).strip(), match.group(2).strip())
                st.toast(f"💾 Memorat: {match.group(1)}")
        
        if ":::NOTE:" in text:
            match = re.search(r":::NOTE:(.*?):::", text)
            if match:
                add_note(match.group(1).strip())
                st.toast("📝 Notiță salvată")
                
        return text
    except Exception as e:
        return f"⚠️ Eroare API: {str(e)}"

# --- INTERFAȚĂ (UI) ---
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS pentru branding iPhone PWA și curățare UI
st.markdown(f"""
    <style>
        /* PWA Meta Tags (emulate via Markdown) */
        @media screen {{
            head {{ display: block; }}
            title {{ content: "{APP_NAME}"; }}
        }}
        
        /* Ascunde elemente inutile dar lasă Sidebar Toggle */
        header[data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
        header[data-testid="stHeader"] > div:nth-child(2) {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        
        /* Design ajustat pentru mobil */
        .block-container {{ padding-top: 1rem; padding-bottom: 5rem; }}
        .stChatMessage {{ border-radius: 12px; border: 1px solid #2e2e2e; }}
        
        /* Iconiță Apple Home Screen */
        link[rel="apple-touch-icon"] {{ content: url("{APP_ICON_URL}"); }}
    </style>
    <link rel="apple-touch-icon" href="{APP_ICON_URL}">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="{APP_NAME}">
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Setări Agent")
    selected_model_name = st.selectbox("Alege Modelul", list(MODELS.keys()), index=0)
    current_model_url = MODELS[selected_model_name]
    
    st.divider()
    mem, notes = get_all_db_data()
    
    st.subheader("🧠 Bază de Date")
    st.write(f"Înregistrări memorie: {len(mem)}")
    st.write(f"Notițe salvate: {len(notes)}")
    
    if st.button("🗑️ Resetare Chat Vizual"):
        st.session_state.messages = []
        st.rerun()
    
    with st.expander("👁️ Vezi Memorie SQL"):
        st.json(mem)
        for n in notes[:10]:
            st.caption(f"• {n}")

# --- MAIN CHAT ---
st.title(f"🤖 {APP_NAME}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Afișare istoric
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input utilizator
if prompt := st.chat_input("Cu ce te pot ajuta?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Gândesc..."):
            ans = ask_ai(prompt, current_model_url)
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

