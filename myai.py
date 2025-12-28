import streamlit as st
import requests
import json
import os
import re
import shutil
import time
import subprocess
import platform
from openai import OpenAI

# --- CONFIGURARE (Preluată din ai.py) ---
API_KEY = "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"
MODELS = {
    "Kat Coder Pro": "kwaipilot/kat-coder-pro:free",
    "DeepSeek R1": "tngtech/deepseek-r1:free",
    "Llama 3.3": "meta-llama/llama-3.3-70b-instruct:free",
    "Mimo V2": "xiaomi/mimo-v2-flash:free"
}
BACKUP_DIR = ".q_backups"
MEMORY_FILE = "q_memory.json"

# Inițializare client
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)

# --- FUNCTII LOGICA (Adaptate din ai.py) ---

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f: return json.load(f)
    return {"projects": {}, "preferences": {}}

def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f: json.dump(memory, f, indent=4)

def apply_surgical_replace(path, old_block, new_block):
    try:
        if not os.path.exists(path): return f"Eroare: Fișier negăsit {path}"
        with open(path, 'r', encoding='utf-8') as f: content = f.read()
        if old_block.strip() in content:
            new_content = content.replace(old_block.strip(), new_block.strip())
            if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
            shutil.copy(path, os.path.join(BACKUP_DIR, f"{int(time.time())}_{os.path.basename(path)}.bak"))
            with open(path, 'w', encoding='utf-8') as f: f.write(new_content)
            return f"PATCH aplicat cu succes pe {path}"
        return "Eroare: Blocul vechi nu a fost găsit."
    except Exception as e: return str(e)

# --- INTERFAȚA STREAMLIT ---
st.set_page_config(page_title="Amazon Q Web Pro", layout="wide")

# Sidebar - Configurații
with st.sidebar:
    st.title("🤖 Agent Control")
    model_choice = st.selectbox("Alege Modelul", list(MODELS.keys()))
    selected_model = MODELS[model_choice]
    
    st.divider()
    st.subheader("🧠 Memorie")
    mem = load_memory()
    st.json(mem["projects"])
    
    if st.button("Șterge Conversația"):
        st.session_state.messages = []
        st.rerun()

# Layout principal
col_chat, col_tools = st.columns([2, 1])

if "messages" not in st.session_state:
    st.session_state.messages = []

# Afișare mesaje
with col_chat:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# Input utilizator
if prompt := st.chat_input("Ce task avem azi?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with col_chat:
        with st.chat_message("user"):
            st.markdown(prompt)

    # Răspuns Agent
    with col_chat:
        with st.chat_message("assistant"):
            resp_container = st.empty()
            full_reply = ""
            
            # Streaming de la OpenRouter
            stream = client.chat.completions.create(
                model=selected_model,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_reply += chunk.choices[0].delta.content
                    resp_container.markdown(full_reply + "▌")
            resp_container.markdown(full_reply)

    # --- EXECUTOR DE ACȚIUNI (Creierul) ---
    with col_tools:
        st.subheader("🛠️ Acțiuni Agent")
        
        # Detecție REPLACE (Logica ta chirurgicală)
        for rem in re.finditer(r":::REPLACE:(.*?)\n<<<<< VECHI\n(.*?)\n=====\n(.*?)\n>>>>>\n:::", full_reply, re.DOTALL):
            path = rem.group(1).strip()
            if st.button(f"Aplică Patch pe {path}"):
                res = apply_surgical_replace(path, rem.group(2), rem.group(3))
                st.success(res)

        # Detecție WRITE
        for wm in re.finditer(r":::WRITE:(.*?)\n(.*?)\n:::", full_reply, re.DOTALL):
            path, content = wm.group(1).strip(), wm.group(2).strip()
            if st.button(f"Creează fișierul {path}"):
                with open(path, 'w') as f: f.write(content)
                st.success(f"Fișier salvat: {path}")

        # Detecție RUN (Cu confirmare UI)
        for runm in re.finditer(r":::RUN:(.*?):::", full_reply):
            cmd = runm.group(1).strip()
            st.warning(f"Comandă detectată: `{cmd}`")
            if st.button("Confirmă Execuția"):
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                st.code(res.stdout + res.stderr)

        # Detecție MEMORIZE
        for mem_match in re.finditer(r":::MEMORIZE:(.*?):(.*?):::", full_reply):
            k, v = mem_match.group(1).strip(), mem_match.group(2).strip()
            mem["projects"][k] = v
            save_memory(mem)
            st.toast(f"Memorie salvată: {k}")

    st.session_state.messages.append({"role": "assistant", "content": full_reply})
