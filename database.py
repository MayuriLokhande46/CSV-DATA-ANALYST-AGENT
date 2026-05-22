import sqlite3
import json
import os

DB_PATH = "statbot_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            plots TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_message(session_id, role, content, plots=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create session if it doesn't exist
    cursor.execute('INSERT OR IGNORE INTO sessions (session_id) VALUES (?)', (session_id,))
    
    # Store lists or dicts as JSON strings
    if isinstance(content, list) or isinstance(content, dict):
        content_str = json.dumps(content)
    else:
        content_str = str(content)
        
    plots_str = json.dumps(plots) if plots else None
    
    cursor.execute('''
        INSERT INTO messages (session_id, role, content, plots)
        VALUES (?, ?, ?, ?)
    ''', (session_id, role, content_str, plots_str))
    
    conn.commit()
    conn.close()

def get_session_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content, plots FROM messages
        WHERE session_id = ? ORDER BY id ASC
    ''', (session_id,))
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for role, content_str, plots_str in rows:
        try:
            content = json.loads(content_str)
        except:
            content = content_str
            
        msg = {"role": role, "content": content}
        if plots_str:
            try:
                plots = json.loads(plots_str)
                if plots:
                    msg["plots"] = plots
            except:
                pass
        messages.append(msg)
    return messages

def clear_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()
