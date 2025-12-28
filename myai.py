import streamlit as st
import requests
import json
import re
import sqlite3
import threading
import asyncio
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- CONFIGURARE BRANDING & API ---
APP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/1698/1698535.png"
APP_NAME = "My AI Agent"
TELEGRAM_TOKEN = "8275670272:AAHltc6EsWkLD3sb2pgApNDOuHbUeA5Mwns"

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("Lipsește OPENROUTER_API_KEY în Secrets!")
    st.stop()

MODELS = {
    "Kat Coder Pro": "kwaipilot/kat-coder-pro:free",
    "DeepSeek R1": "tngtech/deepseek-r1:free",
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct:free"
}

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('agent_memory.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, created_at TEXT)')
    conn.commit()
    conn.close()

def save_memory_sql(key, value):
    conn = sqlite3.connect('agent_memory.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO memory (key, value, updated_at) VALUES (?, ?, ?)", 
              (key, value, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_memory():
    conn = sqlite3.connect('agent_memory.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT key, value FROM memory")
    mem = {row[0]: row[1] for row in c.fetchall()}
    c.execute("SELECT content FROM notes ORDER BY id DESC")
    notes = [row[0] for row in c.fetchall()]
    conn.close()
    return mem, notes

init_db()

# --- AI LOGIC ---
def call_ai(prompt, model_url="kwaipilot/kat-coder-pro:free"):
    mem, notes = get_all_memory()
    system_p = f"Ești un Agent AI cu memorie SQL. Memorie: {json.dumps(mem)}. Notițe: {', '.join(notes[:5])}."
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": model_url, "messages": [{"role": "system", "content": system_p}, {"role": "user", "content": prompt}]}
        )
        resp = r.json()['choices'][0]['message']['content']
        # Procesare memorare
        if ":::MEMORIZE:" in resp:
            match = re.search(r":::MEMORIZE:(.*?):(.*?):::", resp)
            if match: save_memory_sql(match.group(1).strip(), match.group(2).strip())
        return resp
    except:
        return "Eroare la procesarea AI."

# --- TELEGRAM BOT LOGIC ---
async def handle_tg_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    ai_response = call_ai(user_text)
    await update.message.reply_text(ai_response)

def run_telegram_bot():
    # Creăm un nou loop de evenimente pentru acest thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_tg_message))
    app.run_polling()

# Pornim botul doar o singură dată
if "bot_started" not in st.session_state:
    thread = threading.Thread(target=run_telegram_bot, daemon=True)
    thread.start()
    st.session_state.bot_started = True

# --- STREAMLIT UI ---
st.set_page_config(page_title=APP_NAME, page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

st.markdown(f"""
    <head>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-title" content="{APP_NAME}">
        <link rel="apple-touch-icon" href="{APP_ICON_URL}">
    </head>
""", unsafe_allow_html=True)

st.title(f"🤖 {APP_NAME}")
st.caption("Aplicația rulează și botul de Telegram în fundal.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Scrie aici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = call_ai(prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

with st.sidebar:
    st.header("⚙️ Status")
    st.success("Telegram Bot: Activ")
    if st.button("Reset Vizual Chat"):
        st.session_state.messages = []
        st.rerun()

