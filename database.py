import sqlite3
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path="reddit_clone.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela utilizatori
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                karma INTEGER DEFAULT 0,
                bio TEXT DEFAULT ''
            )
        ''')
        
        # Tabela comunități
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communities (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                creator_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                members_count INTEGER DEFAULT 1,
                FOREIGN KEY (creator_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela postări
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                post_type TEXT DEFAULT 'text',
                author_id TEXT,
                community_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                FOREIGN KEY (author_id) REFERENCES users (id),
                FOREIGN KEY (community_id) REFERENCES communities (id)
            )
        ''')
        
        # Tabela comentarii
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                author_id TEXT,
                post_id TEXT,
                parent_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                FOREIGN KEY (author_id) REFERENCES users (id),
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (parent_id) REFERENCES comments (id)
            )
        ''')
        
        # Tabela mesaje private
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                sender_id TEXT,
                receiver_id TEXT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (sender_id) REFERENCES users (id),
                FOREIGN KEY (receiver_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela membri comunități
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS community_members (
                user_id TEXT,
                community_id TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, community_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (community_id) REFERENCES communities (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)

class User:
    def __init__(self, db: Database):
        self.db = db
    
    def create_user(self, username: str, email: str, password: str) -> bool:
        try:
            user_id = str(uuid.uuid4())
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
                (user_id, username, email, password_hash)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, karma, bio FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'karma': user[3],
                'bio': user[4]
            }
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, karma, bio, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'karma': user[3],
                'bio': user[4],
                'created_at': user[5]
            }
        return None

class Community:
    def __init__(self, db: Database):
        self.db = db
    
    def create_community(self, name: str, description: str, creator_id: str) -> bool:
        try:
            community_id = str(uuid.uuid4())
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO communities (id, name, description, creator_id) VALUES (?, ?, ?, ?)",
                (community_id, name, description, creator_id)
            )
            # Adaugă creatorul ca membru
            cursor.execute(
                "INSERT INTO community_members (user_id, community_id) VALUES (?, ?)",
                (creator_id, community_id)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_communities(self) -> List[Dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, members_count, created_at FROM communities ORDER BY members_count DESC"
        )
        communities = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': comm[0],
                'name': comm[1],
                'description': comm[2],
                'members_count': comm[3],
                'created_at': comm[4]
            }
            for comm in communities
        ]

class Post:
    def __init__(self, db: Database):
        self.db = db
    
    def create_post(self, title: str, content: str, post_type: str, author_id: str, community_id: str) -> bool:
        post_id = str(uuid.uuid4())
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO posts (id, title, content, post_type, author_id, community_id) VALUES (?, ?, ?, ?, ?, ?)",
            (post_id, title, content, post_type, author_id, community_id)
        )
        conn.commit()
        conn.close()
        return True
    
    def get_feed_posts(self, limit: int = 20) -> List[Dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.title, p.content, p.post_type, p.created_at, p.upvotes, p.downvotes,
                   u.username, c.name as community_name, p.author_id
            FROM posts p
            JOIN users u ON p.author_id = u.id
            JOIN communities c ON p.community_id = c.id
            ORDER BY p.created_at DESC
            LIMIT ?
        ''', (limit,))
        posts = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': post[0],
                'title': post[1],
                'content': post[2],
                'post_type': post[3],
                'created_at': post[4],
                'upvotes': post[5],
                'downvotes': post[6],
                'author': post[7],
                'community': post[8],
                'author_id': post[9]
            }
            for post in posts
        ]
    
    def delete_post(self, post_id: str, user_id: str) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Verifică dacă utilizatorul este autorul postării
        cursor.execute("SELECT author_id FROM posts WHERE id = ?", (post_id,))
        result = cursor.fetchone()
        
        if result and result[0] == user_id:
            # Șterge comentariile asociate
            cursor.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
            # Șterge postarea
            cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False

class Comment:
    def __init__(self, db: Database):
        self.db = db
    
    def create_comment(self, content: str, author_id: str, post_id: str, parent_id: str = None) -> bool:
        comment_id = str(uuid.uuid4())
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO comments (id, content, author_id, post_id, parent_id) VALUES (?, ?, ?, ?, ?)",
            (comment_id, content, author_id, post_id, parent_id)
        )
        conn.commit()
        conn.close()
        return True
    
    def get_post_comments(self, post_id: str) -> List[Dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.content, c.created_at, c.upvotes, c.downvotes, c.parent_id,
                   u.username
            FROM comments c
            JOIN users u ON c.author_id = u.id
            WHERE c.post_id = ?
            ORDER BY c.created_at ASC
        ''', (post_id,))
        comments = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': comment[0],
                'content': comment[1],
                'created_at': comment[2],
                'upvotes': comment[3],
                'downvotes': comment[4],
                'parent_id': comment[5],
                'author': comment[6]
            }
            for comment in comments
        ]

class Message:
    def __init__(self, db: Database):
        self.db = db
    
    def send_message(self, sender_id: str, receiver_id: str, content: str) -> bool:
        message_id = str(uuid.uuid4())
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (id, sender_id, receiver_id, content) VALUES (?, ?, ?, ?)",
            (message_id, sender_id, receiver_id, content)
        )
        conn.commit()
        conn.close()
        return True
    
    def get_user_messages(self, user_id: str) -> List[Dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.content, m.created_at, m.is_read,
                   sender.username as sender_username,
                   receiver.username as receiver_username
            FROM messages m
            JOIN users sender ON m.sender_id = sender.id
            JOIN users receiver ON m.receiver_id = receiver.id
            WHERE m.sender_id = ? OR m.receiver_id = ?
            ORDER BY m.created_at DESC
        ''', (user_id, user_id))
        messages = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': msg[0],
                'content': msg[1],
                'created_at': msg[2],
                'is_read': msg[3],
                'sender': msg[4],
                'receiver': msg[5]
            }
            for msg in messages
        ]
