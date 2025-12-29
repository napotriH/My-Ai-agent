import streamlit as st
from datetime import datetime, timedelta
import re

def format_time_ago(timestamp_str):
    """Formatează timpul în format 'acum X timp'"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"acum {diff.days} {'zi' if diff.days == 1 else 'zile'}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"acum {hours} {'oră' if hours == 1 else 'ore'}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"acum {minutes} {'minut' if minutes == 1 else 'minute'}"
        else:
            return "acum câteva secunde"
    except:
        return timestamp_str

def validate_email(email):
    """Validează formatul email-ului"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validează numele de utilizator"""
    if len(username) < 3 or len(username) > 20:
        return False, "Numele de utilizator trebuie să aibă între 3 și 20 de caractere"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Numele de utilizator poate conține doar litere, cifre și underscore"
    
    return True, ""

def validate_community_name(name):
    """Validează numele comunității"""
    if len(name) < 3 or len(name) > 21:
        return False, "Numele comunității trebuie să aibă între 3 și 21 de caractere"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        return False, "Numele comunității poate conține doar litere, cifre și underscore"
    
    return True, ""

def truncate_text(text, max_length=200):
    """Trunchiază textul la o lungime maximă"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def get_post_type_icon(post_type):
    """Returnează iconița pentru tipul de postare"""
    icons = {
        'text': '📝',
        'link': '🔗',
        'image': '🖼️',
        'video': '🎥'
    }
    return icons.get(post_type, '📝')

def calculate_karma_score(upvotes, downvotes):
    """Calculează scorul karma"""
    return upvotes - downvotes

def is_valid_url(url):
    """Verifică dacă URL-ul este valid"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def create_notification(user_id, message, notification_type="info"):
    """Creează o notificare pentru utilizator"""
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    notification = {
        'id': len(st.session_state.notifications),
        'user_id': user_id,
        'message': message,
        'type': notification_type,
        'timestamp': datetime.now(),
        'read': False
    }
    
    st.session_state.notifications.append(notification)

def show_notifications():
    """Afișează notificările utilizatorului"""
    if 'notifications' not in st.session_state:
        return
    
    user_notifications = [
        n for n in st.session_state.notifications 
        if n['user_id'] == st.session_state.user['id'] and not n['read']
    ]
    
    if user_notifications:
        st.sidebar.subheader("🔔 Notificări")
        for notification in user_notifications[-3:]:  # Ultimele 3 notificări
            with st.sidebar.container():
                if notification['type'] == 'success':
                    st.success(notification['message'])
                elif notification['type'] == 'error':
                    st.error(notification['message'])
                elif notification['type'] == 'warning':
                    st.warning(notification['message'])
                else:
                    st.info(notification['message'])

def search_posts(query, posts):
    """Caută în postări după titlu și conținut"""
    if not query:
        return posts
    
    query = query.lower()
    filtered_posts = []
    
    for post in posts:
        if (query in post['title'].lower() or 
            query in post['content'].lower() or 
            query in post['author'].lower() or 
            query in post['community'].lower()):
            filtered_posts.append(post)
    
    return filtered_posts

def get_trending_communities(communities):
    """Returnează comunitățile în trending"""
    # Sortează după numărul de membri și activitatea recentă
    return sorted(communities, key=lambda x: x['members_count'], reverse=True)[:5]

def format_number(num):
    """Formatează numerele mari (1000 -> 1k)"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}k"
    else:
        return str(num)

# Configurări pentru tema aplicației
def apply_custom_css():
    """Aplică CSS personalizat pentru aplicație"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4500;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .post-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #fafafa;
    }
    
    .comment-thread {
        border-left: 2px solid #ccc;
        padding-left: 1rem;
        margin-left: 1rem;
    }
    
    .user-karma {
        color: #FF4500;
        font-weight: bold;
    }
    
    .community-tag {
        background-color: #0079d3;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)