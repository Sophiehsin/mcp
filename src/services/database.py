import sqlite3
import uuid
from datetime import datetime
from ..config.settings import DB_PATH

def init_db():
    """初始化資料庫"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_chat_message(session_id, role, content):
    """保存聊天消息到資料庫"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO chat_messages (session_id, role, content)
        VALUES (?, ?, ?)
    ''', (session_id, role, content))
    c.execute('''
        UPDATE chat_sessions 
        SET last_updated = CURRENT_TIMESTAMP 
        WHERE session_id = ?
    ''', (session_id,))
    conn.commit()
    conn.close()

def load_chat_history(session_id):
    """從資料庫載入聊天歷史"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT role, content 
        FROM chat_messages 
        WHERE session_id = ? 
        ORDER BY timestamp ASC
    ''', (session_id,))
    messages = [{"role": role, "content": content} for role, content in c.fetchall()]
    conn.close()
    return messages

def create_new_session():
    """創建新的聊天會話"""
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO chat_sessions (session_id) VALUES (?)', (session_id,))
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions():
    """獲取所有聊天會話"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT session_id, created_at, last_updated 
        FROM chat_sessions 
        ORDER BY last_updated DESC
    ''')
    sessions = c.fetchall()
    conn.close()
    return sessions

def get_recent_messages(session_id, limit=3):
    """獲取最近的對話記錄"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT role, content 
        FROM chat_messages 
        WHERE session_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (session_id, limit))
    messages = [{"role": role, "content": content} for role, content in c.fetchall()]
    conn.close()
    return list(reversed(messages))  # 反轉列表以保持時間順序 