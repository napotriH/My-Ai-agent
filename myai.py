import streamlit as st
import requests
import json
import sqlite3
import re
from datetime import datetime

# --- CONFIGURARE ---
APP_NAME = "AI-Reddit"
APP_ICON = "https://cdn-icons-png.flaticon.com/512/52/52053.png"

try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError:
    st.error("Lipsește OPENROUTER_API_KEY! Adaugă cheia în Streamlit Secrets.")
    st.stop()

# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('social_ai.db', check_same_thread=False)
    c = conn.cursor()
    # Tabel Postări
    c.execute('''CREATE TABLE IF NOT EXISTS posts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, author TEXT, title TEXT, content TEXT, timestamp TEXT)''')
    # Tabel Comentarii
    c.execute('''CREATE TABLE IF NOT EXISTS comments 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, author TEXT, content TEXT, timestamp TEXT)''')
    # Tabel Memorie AI
    c.execute('''CREATE TABLE IF NOT EXISTS ai_memory 
                 (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

def add_post(author, title, content):
    conn = sqlite3.connect('social_ai.db')
    c = conn.cursor()
    c.execute("INSERT INTO posts (author, title, content, timestamp) VALUES (?, ?, ?, ?)",
              (author, title, content, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def add_comment(post_id, author, content):
    conn = sqlite3.connect('social_ai.db')
    c = conn.cursor()
    c.execute("INSERT INTO comments (post_id, author, content, timestamp) VALUES (?, ?, ?, ?)",
              (post_id, author, content, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def get_posts():
    conn = sqlite3.connect('social_ai.db')
    c = conn.cursor()
    c.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = c.fetchall()
    conn.close()
    return posts

def get_comments(post_id):
    conn = sqlite3.connect('social_ai.db')
    c = conn.cursor()
    c.execute("SELECT author, content, timestamp FROM comments WHERE post_id = ? ORDER BY id ASC", (post_id,))
    comments = c.fetchall()
    conn.close()
    return comments

init_db()

# --- AI AGENT LOGIC ---
def get_ai_response(context_text):
    # Luăm memoria din DB
    conn = sqlite3.connect('social_ai.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ai_memory")
    mem = {row[0]: row[1] for row in c.fetchall()}
    conn.close()

    system_prompt = (
        f"Ești asistentul oficial al rețelei {APP_NAME}. "
        f"Memoria ta actuală: {json.dumps(mem)}. "
        "Dacă utilizatorul îți cere să reții ceva, folosește :::MEMORIZE:cheie:valoare::: în răspuns."
    )

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "kwaipilot/kat-coder-pro:free",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context_text}
                ]
            }
        )
        ans = r.json()['choices'][0]['message']['content']
        
        # Procesare memorie
        if ":::MEMORIZE:" in ans:
            match = re.search(r":::MEMORIZE:(.*?):(.*?):::", ans)
            if match:
                conn = sqlite3.connect('social_ai.db')
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO ai_memory (key, value) VALUES (?, ?)", 
                          (match.group(1).strip(), match.group(2).strip()))
                conn.commit()
                conn.close()
        return ans
    except:
        return "🤖 AI-ul este offline momentan."

# --- UI UI UI ---
st.set_page_config(page_title=APP_NAME, page_icon="📝", layout="centered")

# CSS pentru aspect de Reddit
st.markdown("""
    <style>
    .post-container {
        background-color: #1A1A1B;
        border: 1px solid #343536;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .post-title { font-size: 20px; font-weight: bold; color: #D7DADC; }
    .post-meta { font-size: 12px; color: #818384; margin-bottom: 10px; }
    .comment-box {
        margin-left: 20px;
        border-left: 2px solid #343536;
        padding-left: 15px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Branding PWA
st.markdown(f"""
    <head>
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-title" content="{APP_NAME}">
        <link rel="apple-touch-icon" href="{APP_ICON}">
    </head>
""", unsafe_allow_html=True)

st.title(f"🏠 {APP_NAME}")

# Tabs: Feed, Postare Nouă, Asistent AI
tab1, tab2, tab3 = st.tabs(["🔥 Feed", "➕ Creează", "🤖 Asistent"])

with tab1:
    posts = get_posts()
    if not posts:
        st.info("Nicio postare încă. Fii primul care scrie ceva!")
    
    for p_id, p_author, p_title, p_content, p_time in posts:
        with st.container():
            st.markdown(f"""
            <div class="post-container">
                <div class="post-meta">Postat de u/{p_author} • {p_time}</div>
                <div class="post-title">{p_title}</div>
                <p style="color: #D7DADC; margin-top:10px;">{p_content}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Afișare comentarii
            comments = get_comments(p_id)
            for c_author, c_content, c_time in comments:
                st.markdown(f"""
                <div class="comment-box">
                    <span style="font-size: 11px; color: #818384;">u/{c_author} • {c_time}</span><br>
                    <span style="color: #D7DADC;">{c_content}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Formular comentariu rapid
            with st.expander("Comentează"):
                c_text = st.text_area("Scrie un comentariu...", key=f"c_{p_id}")
                if st.button("Trimite", key=f"b_{p_id}"):
                    if c_text:
                        add_comment(p_id, "Eu", c_text)
                        st.rerun()

with tab2:
    st.header("Creează o postare nouă")
    t_input = st.text_input("Titlu")
    c_input = st.text_area("Conținut (Markdown suportat)")
    if st.button("Postează"):
        if t_input and c_input:
            add_post("Eu", t_input, c_input)
            st.success("Postare publicată!")
            st.rerun()

with tab3:
    st.header("Discută cu Agentul AI")
    st.write("Acest agent are acces la baza de date și îți poate răspunde la întrebări despre comunitate.")
    
    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = []

    for m in st.session_state.ai_chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if ai_prompt := st.chat_input("Întreabă AI-ul..."):
        st.session_state.ai_chat.append({"role": "user", "content": ai_prompt})
        with st.chat_message("user"): st.write(ai_prompt)
        
        with st.chat_message("assistant"):
            resp = get_ai_response(ai_prompt)
            st.write(resp)
            st.session_state.ai_chat.append({"role": "assistant", "content": resp})

with st.sidebar:
    st.image(APP_ICON, width=100)
    st.title("Profil")
    st.write("u/Eu")
    st.divider()
    if st.button("Reset Bază de Date"):
        import os
        if os.path.exists("social_ai.db"):
            os.remove("social_ai.db")
            init_db()
            st.rerun()

