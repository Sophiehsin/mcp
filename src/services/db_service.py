import sqlite3
import uuid
from datetime import datetime

def init_db():
    """初始化資料庫"""
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    
    # 創建聊天會話表
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP,
            mode TEXT
        )
    ''')
    
    # 創建聊天訊息表
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_message(session_id, role, content):
    """儲存聊天訊息"""
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO chat_messages (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (session_id, role, content, datetime.now()))
    
    conn.commit()
    conn.close()

def load_chat_history(session_id, limit=3):
    """載入最近的聊天歷史"""
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT role, content
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (session_id, limit))
    
    messages = c.fetchall()
    conn.close()
    
    # 轉換成 Together API 需要的格式
    return [{"role": role, "content": content} for role, content in reversed(messages)]

def create_session(mode="AI 幫你規劃"):
    """創建新的聊天會話"""
    session_id = str(uuid.uuid4())
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO chat_sessions (session_id, created_at, mode)
        VALUES (?, ?, ?)
    ''', (session_id, datetime.now(), mode))
    
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions():
    """獲取所有聊天會話"""
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT session_id, created_at, mode
        FROM chat_sessions
        ORDER BY created_at DESC
    ''')
    
    sessions = c.fetchall()
    conn.close()
    return sessions

def delete_session(session_id):
    """刪除聊天會話及其所有訊息"""
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    
    # 先刪除相關的訊息
    c.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))
    # 再刪除會話
    c.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))
    
    conn.commit()
    conn.close() 