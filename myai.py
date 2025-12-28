import streamlit as st
import requests
import json
import re
from openai import OpenAI

# --- CONFIGURARE (Preluată din ai.py) ---
API_KEY = "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"
MODELS = {
    "Kat Coder (Pro)": "kwaipilot/kat-coder-pro:free",
    "DeepSeek R1": "tngtech/deepseek-r1:free",
    "Llama 3.3": "meta-llama/llama-3.3-70b-instruct:free",
    "Mimo V2": "xiaomi/mimo-v2-flash:free"
}

# Inițializare Client OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

st.set_page_config(page_title="Amazon Q Web Pro", layout="wide")

# --- UI SIDEBAR ---
with st.sidebar:
    st.title("🤖 Configurare Agent")
    model_label = st.selectbox("Alege Modelul:", list(MODELS.keys()))
    selected_model = MODELS[model_label]
    st.info(f"Model activ: {selected_model}")
    
    if st.button("Șterge Istoric Chat"):
        st.session_state.messages = []
        st.rerun()

# --- LOGICĂ CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afișare mesaje existente
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input utilizator
if prompt := st.chat_input("Scrie o comandă sau o întrebare..."):
    # Adăugăm mesajul utilizatorului
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Răspuns Agent
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Apel către OpenRouter (folosind lista ta de modele)
        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
        
        # Procesare Protocol Operațiuni (Surgical Replace, Write etc.)
        # Aici putem integra funcțiile tale: apply_surgical_replace, apply_full_write
        if ":::WRITE:" in full_response:
            st.warning("Agentul încearcă să scrie un fișier pe server.")
            # Logica ta de scriere poate fi apelată aici

    st.session_state.messages.append({"role": "assistant", "content": full_response})
