import streamlit as st
import requests
import json
import re
import sqlite3
from datetime import datetime

# --- CONFIGURARE SECRETS ---
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("Lipsește cheia API! Adaugă OPENROUTER_API_KEY în Streamlit Secrets.")
    st.stop()

MODELS = {
    "Kat Coder Pro": "kwaipilot/kat-coder-pro:free",
    "DeepSeek R1": "tngtech/deepseek-r1:free",
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct:free",
    "Mimo V2 Flash": "xiaomi/mimo-v2-flash:free"
}

st.set_page_config(page_title="AI Agent SQL", page_icon="💾", layout="wide")

# --- DATABASE ENGINE (SQLite) ---
def init_db():
    conn = sqlite3.connect('agent_memory.db')
    c = conn.cursor()
    # Tabel pentru memorie (key-value)
    c.execute('''CREATE TABLE IF NOT EXISTS memory 
                 (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)''')
    # Tabel pentru notițe
    c.execute('''CREATE TABLE IF NOT EXISTS notes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def save_memory_sql(key, value):
    conn = sqlite3.connect('agent_memory.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO memory (key, value, updated_at) VALUES (?, ?, ?)", (key, value, now))
    conn.commit()
    conn.close()

def add_note_sql(content):
    conn = sqlite3.connect('agent_memory.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO notes (content, created_at) VALUES (?, ?)", (content, now))
    conn.commit()
    conn.close()

def get_all_memory():
    conn = sqlite3.connect('agent_memory.db')
    c = conn.cursor()
    c.execute("SELECT key, value FROM memory")
    data = {row[0]: row[1] for row in c.fetchall()}
    c.execute("SELECT content FROM notes ORDER BY id DESC")
    notes = [row[0] for row in c.fetchall()]
    conn.close()
    return data, notes

# Inițializăm baza de date la pornire
init_db()

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CORE API ---
def call_openrouter(prompt, model_url):
    mem_data, notes_data = get_all_memory()
    
    system_prompt = (
        "Ești un Agent AI cu memorie SQL persistentă.\n"
        f"Memorie Proiecte: {json.dumps(mem_data)}\n"
        f"Notițe recente: {', '.join(notes_data[:5])}\n"
        "Comenzi: :::MEMORIZE:cheie:valoare::: și :::NOTE:text:::"
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in st.session_state.messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://streamlit.io"
            },
            json={"model": model_url, "messages": messages[-12:]}
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Eroare: {str(e)}"

# --- UI ---
with st.sidebar:
    st.title("💾 SQL Agent")
    selected_model = st.selectbox("Model", list(MODELS.keys()))
    
    st.divider()
    mem_data, notes_data = get_all_memory()
    
    st.subheader("📊 Statistici DB")
    st.write(f"Proiecte memorate: {len(mem_data)}")
    st.write(f"Notițe totale: {len(notes_data)}")
    
    if st.button("🗑️ Reset Vizual Chat"):
        st.session_state.messages = []
        st.rerun()

st.title("🤖 Agent AI cu stocare SQLite")

# Afișare chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Introdu o comandă sau întrebare..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Accesare bază de date și API..."):
            response = call_openrouter(prompt, MODELS[selected_model])
            
            # Procesare automată a comenzilor din răspunsul AI-ului
            if ":::MEMORIZE:" in response:
                m = re.search(r":::MEMORIZE:(.*?):(.*?):::", response)
                if m:
                    save_memory_sql(m.group(1).strip(), m.group(2).strip())
                    st.toast(f"💾 Salvat în DB: {m.group(1)}")
            
            if ":::NOTE:" in response:
                n = re.search(r":::NOTE:(.*?):::", response)
                if n:
                    add_note_sql(n.group(1).strip())
                    st.toast("📝 Notiță adăugată în DB")

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Secțiune pentru vizualizarea datelor din SQLite
if notes_data:
    with st.expander("📓 Vezi toate notițele din SQLite"):
        for note in notes_data:
            st.text(f"• {note}")

