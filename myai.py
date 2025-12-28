import streamlit as st
import requests
import json
import re

# --- CONFIGURARE SECRETS ---
# Nu mai scriem cheia aici. O vom adăuga în interfața Streamlit Cloud.
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

st.set_page_config(page_title="AI Agent Pro", page_icon="🤖", layout="wide")

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    st.session_state.memory = {"projects": {}, "preferences": {}}

# --- UTILS ---
def call_openrouter(prompt, model_url):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Streamlit AI Agent"
    }
    
    system_prompt = (
        f"Ești un Agent AI Avansat.\n"
        f"Context Memorie: {json.dumps(st.session_state.memory)}\n"
        "Fii util și concis."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in st.session_state.messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            url, 
            headers=headers, 
            json={
                "model": model_url,
                "messages": messages[-10:],
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Eroare API: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Setări Agent")
    selected_model_name = st.selectbox("Alege Modelul", list(MODELS.keys()))
    model_url = MODELS[selected_model_name]
    
    if st.button("Șterge Istoricul"):
        st.session_state.messages = []
        st.rerun()
    
    st.subheader("🧠 Memorie")
    st.json(st.session_state.memory)

# --- MAIN UI ---
st.title(f"🚀 AI Agent - {selected_model_name}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Scrie ceva..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Se gândește..."):
            response = call_openrouter(prompt, model_url)
            # Logica de memorare
            mem_match = re.search(r":::MEMORIZE:(.*?):(.*?):::", response)
            if mem_match:
                key, val = mem_match.group(1).strip(), mem_match.group(2).strip()
                st.session_state.memory["projects"][key] = val
                st.toast(f"Memorie salvată: {key}")

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

