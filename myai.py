import streamlit as st
import requests
import json
import re
import sqlite3
from datetime import datetime

# --- CONFIGURARE BRANDING ---
# Înlocuiește acest URL cu link-ul către logo-ul tău (pătrat, minim 180x180px)
APP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/1698/1698535.png" 
APP_NAME = "My AI Agent"

# --- CONFIGURARE SECRETS ---
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("Lipsește cheia API în Streamlit Secrets!")
    st.stop()

MODELS = {
    "Kat Coder Pro": "kwaipilot/kat-coder-pro:free",
    "DeepSeek R1": "tngtech/deepseek-r1:free",
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct:free",
    "Mimo V2 Flash": "xiaomi/mimo-v2-flash:free"
}

# --- SETĂRI PAGINĂ ȘI PWA ---
st.set_page_config(
    page_title=APP_NAME, 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Injectare Meta-Tag-uri pentru iOS (Home Screen)
# Acestea forțează iPhone-ul să recunoască aplicația cu numele și iconița ta
st.markdown(f"""
    <head>
        <title>{APP_NAME}</title>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="{APP_NAME}">
        <link rel="apple-touch-icon" href="{APP_ICON_URL}">
        <style>
            /* Ascunde meniul Streamlit (opțional, pentru aspect curat) */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            
            /* Ajustare spațiu pentru bara de status iOS */
            .stApp {{
                margin-top: 20px;
            }}
        </style>
    </head>
""", unsafe_allow_html=True)

# --- DATABASE ENGINE (SQLite) ---
def init_db():
    conn = sqlite3.connect('agent_memory.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, created_at TEXT)')
    conn.commit()
    conn.close()

def save_memory_sql(key, value):
    conn = sqlite3.connect('agent_memory.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO memory (key, value, updated_at) VALUES (?, ?, ?)", 
              (key, value, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def add_note_sql(content):
    conn = sqlite3.connect('agent_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (content, created_at) VALUES (?, ?)", 
              (content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_memory():
    conn = sqlite3.connect('agent_memory.db')
    c = conn.cursor()
    c.execute("SELECT key, value FROM memory")
    mem = {row[0]: row[1] for row in c.fetchall()}
    c.execute("SELECT content FROM notes ORDER BY id DESC")
    notes = [row[0] for row in c.fetchall()]
    conn.close()
    return mem, notes

init_db()

# --- STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CHAT LOGIC ---
def call_openrouter(prompt, model_url):
    mem_data, notes_data = get_all_memory()
    system_prompt = f"Ești un Agent AI personalizat. Memorie: {json.dumps(mem_data)}. Notițe: {', '.join(notes_data[:5])}."
    
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": model_url, "messages": [{"role": "system", "content": system_prompt}] + st.session_state.messages[-10:] + [{"role": "user", "content": prompt}]}
        )
        return r.json()['choices'][0]['message']['content']
    except:
        return "Eroare la conectarea cu creierul AI."

# --- UI ---
st.title(f"🤖 {APP_NAME}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Scrie ceva..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = call_openrouter(prompt, MODELS[st.sidebar.selectbox("Model", list(MODELS.keys()), key="model_sel")])
        
        # Extracție comenzi
        if ":::MEMORIZE:" in response:
            m = re.search(r":::MEMORIZE:(.*?):(.*?):::", response)
            if m: save_memory_sql(m.group(1).strip(), m.group(2).strip())
        if ":::NOTE:" in response:
            n = re.search(r":::NOTE:(.*?):::", response)
            if n: add_note_sql(n.group(1).strip())

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with st.sidebar:
    st.write("---")
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

