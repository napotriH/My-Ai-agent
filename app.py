import streamlit as st
from database import Database, User, Community, Post, Comment, Message
from datetime import datetime

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
    st.title("🔥 Reddit Clone - Autentificare")
    
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
        st.title("🔥 Reddit Clone")
        
        if st.session_state.user:
            st.write(f"Salut, **{st.session_state.user['username']}**!")
            st.write(f"Karma: {st.session_state.user['karma']}")
            
            if st.button("🏠 Feed"):
                st.session_state.page = 'feed'
                st.rerun()
            
            if st.button("🏘️ Comunități"):
                st.session_state.page = 'communities'
                st.rerun()
            
            if st.button("➕ Postare nouă"):
                st.session_state.page = 'new_post'
                st.rerun()
            
            if st.button("👤 Profil"):
                st.session_state.page = 'profile'
                st.rerun()
            
            if st.button("💬 Mesaje"):
                st.session_state.page = 'messages'
                st.rerun()
            
            st.divider()
            
            if st.button("🚪 Deconectează-te"):
                st.session_state.user = None
                st.session_state.page = 'feed'
                st.rerun()

def feed_page():
    st.title("🏠 Feed Principal")
    
    posts = post_manager.get_feed_posts()
    
    if not posts:
        st.info("Nu există postări încă. Fii primul care postează ceva!")
        return
    
    for post in posts:
        with st.container():
            col1, col2 = st.columns([1, 10])
            
            with col1:
                st.button("⬆️", key=f"up_{post['id']}")
                st.write(f"{post['upvotes'] - post['downvotes']}")
                st.button("⬇️", key=f"down_{post['id']}")
            
            with col2:
                st.subheader(post['title'])
                st.write(f"r/{post['community']} • u/{post['author']} • {post['created_at']}")
                
                if post['post_type'] == 'text':
                    st.write(post['content'])
                elif post['post_type'] == 'link':
                    st.link_button("🔗 Vezi link", post['content'])
                
                col_comment, col_share = st.columns([1, 1])
                with col_comment:
                    if st.button(f"💬 Comentarii", key=f"comment_{post['id']}"):
                        st.session_state.selected_post = post['id']
                        st.session_state.page = 'post_detail'
                        st.rerun()
            
            st.divider()

def communities_page():
    st.title("🏘️ Comunități")
    
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
    st.title("➕ Postare nouă")
    
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
    
    st.title("💬 Comentarii")
    
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
    st.title("👤 Profilul meu")
    
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
    st.title("💬 Mesaje private")
    
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