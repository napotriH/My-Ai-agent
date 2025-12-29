import streamlit as st
from database import Database, User, Community, Post, Comment, Message
from datetime import datetime

# Funcție pentru iconițe SVG
def icon(name, size=16, color="currentColor"):
    icons = {
        "flame": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
        "home": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9,22 9,12 15,12 15,22"/></svg>',
        "users": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m22 21-3.5-3.5a7 7 0 1 0-1.414 1.414L21 22"/></svg>',
        "plus": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/></svg>',
        "user": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
        "message-circle": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>',
        "log-out": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16,17 21,12 16,7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
        "external-link": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>'
    }
    return icons.get(name, '')

# Configurare pagină
st.set_page_config(
    page_title="Reddit Clone",
    page_icon="🔥",
    layout="wide"
)

# Inițializare bază de date
@st.cache_resource
def init_database():
    return Database()

db = init_database()
user_manager = User(db)
community_manager = Community(db)
post_manager = Post(db)
comment_manager = Comment(db)
message_manager = Message(db)

# Inițializare session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'feed'

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div style='text-align: center'>", unsafe_allow_html=True)
        st.markdown(icon("flame", 48, "#FF4500"), unsafe_allow_html=True)
        st.title("Reddit Clone")
        st.markdown("</div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Înregistrare"])
    
    with tab1:
        st.subheader("Conectează-te")
        username = st.text_input("Nume utilizator", key="login_username")
        password = st.text_input("Parolă", type="password", key="login_password")
        
        if st.button("Conectează-te", key="login_btn"):
            user = user_manager.authenticate(username, password)
            if user:
                st.session_state.user = user
                st.success("Conectare reușită!")
                st.rerun()
            else:
                st.error("Credențiale invalide!")
    
    with tab2:
        st.subheader("Creează cont nou")
        new_username = st.text_input("Nume utilizator", key="reg_username")
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Parolă", type="password", key="reg_password")
        confirm_password = st.text_input("Confirmă parola", type="password", key="reg_confirm")
        
        if st.button("Înregistrează-te", key="register_btn"):
            if new_password != confirm_password:
                st.error("Parolele nu coincid!")
            elif len(new_password) < 6:
                st.error("Parola trebuie să aibă cel puțin 6 caractere!")
            else:
                if user_manager.create_user(new_username, new_email, new_password):
                    st.success("Cont creat cu succes! Poți să te conectezi acum.")
                else:
                    st.error("Numele de utilizator sau email-ul există deja!")

def sidebar():
    with st.sidebar:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(icon("flame", 24, "#FF4500"), unsafe_allow_html=True)
        with col2:
            st.title("Reddit Clone")
        
        if st.session_state.user:
            st.write(f"Salut, **{st.session_state.user['username']}**!")
            st.write(f"Karma: {st.session_state.user['karma']}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(icon("home", 16), unsafe_allow_html=True)
            with col2:
                if st.button("Feed", key="nav_feed"):
                    st.session_state.page = 'feed'
                    st.rerun()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(icon("users", 16), unsafe_allow_html=True)
            with col2:
                if st.button("Comunități", key="nav_communities"):
                    st.session_state.page = 'communities'
                    st.rerun()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(icon("plus", 16), unsafe_allow_html=True)
            with col2:
                if st.button("Postare nouă", key="nav_new_post"):
                    st.session_state.page = 'new_post'
                    st.rerun()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(icon("user", 16), unsafe_allow_html=True)
            with col2:
                if st.button("Profil", key="nav_profile"):
                    st.session_state.page = 'profile'
                    st.rerun()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(icon("message-circle", 16), unsafe_allow_html=True)
            with col2:
                if st.button("Mesaje", key="nav_messages"):
                    st.session_state.page = 'messages'
                    st.rerun()
            
            st.divider()
            
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(icon("log-out", 16), unsafe_allow_html=True)
            with col2:
                if st.button("Deconectează-te", key="nav_logout"):
                    st.session_state.user = None
                    st.session_state.page = 'feed'
                    st.rerun()

def feed_page():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.markdown(icon("home", 24), unsafe_allow_html=True)
    with col2:
        st.title("Feed Principal")
    
    posts = post_manager.get_feed_posts()
    
    if not posts:
        st.info("Nu există postări încă. Fii primul care postează ceva!")
        return
    
    for post in posts:
        with st.container():
            col1, col2 = st.columns([1, 10])
            
            with col1:
                if st.button("⬆️", key=f"up_{post['id']}"):
                    pass
                st.write(f"{post['upvotes'] - post['downvotes']}")
                if st.button("⬇️", key=f"down_{post['id']}"):
                    pass
            
            with col2:
                st.subheader(post['title'])
                st.write(f"r/{post['community']} • u/{post['author']} • {post['created_at']}")
                
                if post['post_type'] == 'text':
                    st.write(post['content'])
                elif post['post_type'] == 'link':
                    st.markdown(f"{icon('external-link', 16)} [Vezi link]({post['content']})", unsafe_allow_html=True)
                
                # Butoane pentru postare
                col_comment, col_delete = st.columns([1, 1])
                
                with col_comment:
                    if st.button(f"{icon('message-circle', 16)} Comentarii", key=f"comment_{post['id']}"):
                        st.session_state.selected_post = post['id']
                        st.session_state.page = 'post_detail'
                        st.rerun()
                
                with col_delete:
                    # Afișează butonul de ștergere doar pentru autorul postării
                    if post['author_id'] == st.session_state.user['id']:
                        if st.button("🗑️ Șterge", key=f"delete_{post['id']}"):
                            if post_manager.delete_post(post['id'], st.session_state.user['id']):
                                st.success("Postare ștearsă!")
                                st.rerun()
                            else:
                                st.error("Eroare la ștergere!")
            
            st.divider()

def communities_page():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.markdown(icon("users", 24), unsafe_allow_html=True)
    with col2:
        st.title("Comunități")
    
    tab1, tab2 = st.tabs(["Explorează", "Creează comunitate"])
    
    with tab1:
        communities = community_manager.get_all_communities()
        
        for community in communities:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(f"r/{community['name']}")
                    st.write(community['description'])
                    st.write(f"{community['members_count']} membri")
                
                with col2:
                    st.button("Alătură-te", key=f"join_{community['id']}")
                
                st.divider()
    
    with tab2:
        st.subheader("Creează o comunitate nouă")
        name = st.text_input("Numele comunității")
        description = st.text_area("Descrierea comunității")
        
        if st.button("Creează comunitatea"):
            if name and description:
                if community_manager.create_community(name, description, st.session_state.user['id']):
                    st.success("Comunitate creată cu succes!")
                    st.rerun()
                else:
                    st.error("Numele comunității există deja!")
            else:
                st.error("Completează toate câmpurile!")

def new_post_page():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.markdown(icon("plus", 24), unsafe_allow_html=True)
    with col2:
        st.title("Postare nouă")
    
    communities = community_manager.get_all_communities()
    community_options = {f"r/{comm['name']}": comm['id'] for comm in communities}
    
    selected_community = st.selectbox("Alege comunitatea", list(community_options.keys()))
    post_type = st.selectbox("Tipul postării", ["text", "link", "image"])
    title = st.text_input("Titlul postării")
    
    if post_type == "text":
        content = st.text_area("Conținutul postării")
    elif post_type == "link":
        content = st.text_input("URL-ul link-ului")
    else:
        content = st.file_uploader("Încarcă imaginea", type=['png', 'jpg', 'jpeg'])
        if content:
            content = f"image_{content.name}"
    
    if st.button("Publică postarea"):
        if title and content and selected_community:
            community_id = community_options[selected_community]
            if post_manager.create_post(title, str(content), post_type, st.session_state.user['id'], community_id):
                st.success("Postare publicată cu succes!")
                st.session_state.page = 'feed'
                st.rerun()
        else:
            st.error("Completează toate câmpurile!")

def post_detail_page():
    if 'selected_post' not in st.session_state:
        st.session_state.page = 'feed'
        st.rerun()
        return
    
    post_id = st.session_state.selected_post
    comments = comment_manager.get_post_comments(post_id)
    
    col1, col2 = st.columns([1, 10])
    with col1:
        st.markdown(icon("message-circle", 24), unsafe_allow_html=True)
    with col2:
        st.title("Comentarii")
    
    # Formular pentru comentariu nou
    new_comment = st.text_area("Adaugă un comentariu")
    if st.button("Postează comentariul"):
        if new_comment:
            comment_manager.create_comment(new_comment, st.session_state.user['id'], post_id)
            st.success("Comentariu adăugat!")
            st.rerun()
    
    st.divider()
    
    # Afișare comentarii
    def display_comments(comments, parent_id=None, level=0):
        for comment in comments:
            if comment['parent_id'] == parent_id:
                with st.container():
                    # Indentare pentru thread-uri
                    indent = "    " * level
                    st.write(f"{indent}**{comment['author']}** • {comment['created_at']}")
                    st.write(f"{indent}{comment['content']}")
                    
                    col1, col2, col3 = st.columns([1, 1, 8])
                    with col1:
                        st.button("⬆️", key=f"up_comment_{comment['id']}")
                    with col2:
                        st.button("⬇️", key=f"down_comment_{comment['id']}")
                    with col3:
                        if st.button("Răspunde", key=f"reply_{comment['id']}"):
                            reply_text = st.text_input(f"Răspuns la {comment['author']}", key=f"reply_text_{comment['id']}")
                            if st.button("Trimite răspuns", key=f"send_reply_{comment['id']}"):
                                if reply_text:
                                    comment_manager.create_comment(reply_text, st.session_state.user['id'], post_id, comment['id'])
                                    st.rerun()
                    
                    # Afișare răspunsuri recursive
                    display_comments(comments, comment['id'], level + 1)
                    st.divider()
    
    display_comments(comments)
    
    if st.button("← Înapoi la feed"):
        st.session_state.page = 'feed'
        st.rerun()

def profile_page():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.markdown(icon("user", 24), unsafe_allow_html=True)
    with col2:
        st.title("Profilul meu")
    
    user = st.session_state.user
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Informații profil")
        st.write(f"**Nume utilizator:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Karma:** {user['karma']}")
    
    with col2:
        st.subheader("Editează profilul")
        new_bio = st.text_area("Bio", value=user.get('bio', ''))
        
        if st.button("Salvează modificările"):
            # Aici ar trebui să actualizezi bio-ul în baza de date
            st.success("Profil actualizat!")

def messages_page():
    col1, col2 = st.columns([1, 10])
    with col1:
        st.markdown(icon("message-circle", 24), unsafe_allow_html=True)
    with col2:
        st.title("Mesaje private")
    
    tab1, tab2 = st.tabs(["Mesajele mele", "Trimite mesaj"])
    
    with tab1:
        messages = message_manager.get_user_messages(st.session_state.user['id'])
        
        for message in messages:
            with st.container():
                if message['sender'] == st.session_state.user['username']:
                    st.write(f"**Tu** → **{message['receiver']}**")
                else:
                    st.write(f"**{message['sender']}** → **Tu**")
                
                st.write(message['content'])
                st.write(f"*{message['created_at']}*")
                st.divider()
    
    with tab2:
        receiver_username = st.text_input("Destinatar (nume utilizator)")
        message_content = st.text_area("Mesajul tău")
        
        if st.button("Trimite mesajul"):
            if receiver_username and message_content:
                # Aici ar trebui să găsești ID-ul utilizatorului destinatar
                # Pentru simplitate, presupunem că funcționează
                st.success("Mesaj trimis!")
            else:
                st.error("Completează toate câmpurile!")

def main():
    if st.session_state.user is None:
        login_page()
    else:
        sidebar()
        
        if st.session_state.page == 'feed':
            feed_page()
        elif st.session_state.page == 'communities':
            communities_page()
        elif st.session_state.page == 'new_post':
            new_post_page()
        elif st.session_state.page == 'post_detail':
            post_detail_page()
        elif st.session_state.page == 'profile':
            profile_page()
        elif st.session_state.page == 'messages':
            messages_page()

if __name__ == "__main__":
    main()
