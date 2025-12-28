import streamlit as st

# Lărgim pagina pentru a folosi tot ecranul
st.set_page_config(layout="wide")

# 1. SIDEBAR (Setările de backend)
with st.sidebar:
    st.header("⚙️ Configurare")
    api_key = st.text_input("OpenRouter Key", type="password")
    model = st.selectbox("Model AI", ["Claude 3.5 Sonnet", "GPT-4o"])
    temp = st.slider("Creativitate (Temperature)", 0.0, 1.0, 0.7)
    st.divider()
    if st.button("Șterge Istoric"):
        st.session_state.messages = []

# 2. COLONANE (Organizarea vizuală)
col_chat, col_info = st.columns([2, 1])  # Chat-ul ocupă 2/3, Info 1/3

with col_chat:
    st.subheader("💬 Conversație cu Agentul")
    # Aici ar veni logica de afișare a mesajelor (ca în exemplul anterior)
    st.info("Mesajele vor apărea aici...")

with col_info:
    st.subheader("🧠 Status Agent")
    # Aici poți afișa ce "gândește" agentul în spate
    with st.expander("Vezi pașii de procesare", expanded=True):
        st.write("1. Analizez cererea utilizatorului...")
        st.write("2. Interoghez baza de date...")
        st.write("3. Generez răspuns final...")

        st.metric(label="Tokeni folosiți", value="1,240", delta="-50")