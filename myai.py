import streamlit as st
import requests
import json
import re
import streamlit.components.v1 as components

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

st.set_page_config(
    page_title="AI Agent Pro", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- PWA CAPABILITIES (Injection) ---
# Injectăm Manifest-ul și Service Worker-ul pentru a permite instalarea pe ecranul principal
pwa_html = """
<link rel="manifest" href="https://raw.githubusercontent.com/username/repo/main/manifest.json">
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('https://raw.githubusercontent.com/username/repo/main/sw.js');
    });
  }
</script>
"""
# Notă: Pentru PWA complet, fișierele manifest.json și sw.js trebuie să fie servite de același domeniu.
# Streamlit Cloud are limitări aici, dar putem "păcăli" browserul cu un buton de instalare sau meta tags.

st.markdown('<meta name="apple-mobile-web-app-capable" content="yes">', unsafe_allow_html=True)
st.markdown('<meta name="apple-mobile-web-app-status-bar-style" content="black">', unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    # Memoria acum include și comenzi de gestionare
    st.session_state.memory = {"projects": {}, "preferences": {}, "notes": []}

# --- UTILS ---
def call_openrouter(prompt, model_url):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "Streamlit AI Agent PWA"
    }
    
    system_prompt = (
        "Ești un Agent AI personalizat cu memorie persistentă pe sesiune.\n"
        f"Memorie curentă: {json.dumps(st.session_state.memory)}\n"
        "Comenzi speciale pe care le poți folosi în răspuns:\n"
        "1. :::MEMORIZE:cheie:valoare::: -> pentru a salva date\n"
        "2. :::NOTE:text::: -> pentru a adăuga o notiță rapidă\n"
        "Fii concis și eficient."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in st.session_state.messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        response = requests.post(url, headers=headers, json={"model": model_url, "messages": messages[-15:]}, timeout=60)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Eroare API: {str(e)}"

# --- UI LOGIC ---
with st.sidebar:
    st.title("⚙️ Configurare")
    selected_model_name = st.selectbox("Model AI", list(MODELS.keys()))
    model_url = MODELS[selected_model_name]
    
    st.divider()
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

    st.subheader("🧠 Memorie Activă")
    if st.checkbox("Arată date brute"):
        st.json(st.session_state.memory)
    
    for key, val in st.session_state.memory["projects"].items():
        st.caption(f"**{key}**: {val}")

# --- MAIN CHAT ---
st.title("🤖 AI Agent Pro")

# Afișăm istoricul
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Scrie aici..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agentul lucrează..."):
            response = call_openrouter(prompt, model_url)
            
            # Procesare comenzi memorie
            m_match = re.search(r":::MEMORIZE:(.*?):(.*?):::", response)
            if m_match:
                st.session_state.memory["projects"][m_match.group(1).strip()] = m_match.group(2).strip()
                st.toast(f"✅ Memorat: {m_match.group(1)}")
            
            n_match = re.search(r":::NOTE:(.*?):::", response)
            if n_match:
                st.session_state.memory["notes"].append(n_match.group(1).strip())
                st.toast("📝 Notiță adăugată")

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

