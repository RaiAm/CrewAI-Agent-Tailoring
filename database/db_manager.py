import sqlite3
import os

DB_PATH = "resumes.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            base_resume_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            job_title TEXT,
            company_name TEXT,
            job_input TEXT,
            company_intelligence TEXT,
            tailored_resume_markdown TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_candidates():
    conn = get_db_connection()
    candidates = conn.execute("SELECT * FROM candidates ORDER BY name").fetchall()
    conn.close()
    return candidates

def create_candidate(name: str, base_resume_text: str = ""):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO candidates (name, base_resume_text) VALUES (?, ?)", (name, base_resume_text))
        conn.commit()
        candidate_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        candidate_id = None
    finally:
        conn.close()
    return candidate_id

def update_base_resume(candidate_id: int, text: str):
    conn = get_db_connection()
    conn.execute("UPDATE candidates SET base_resume_text = ? WHERE id = ?", (text, candidate_id))
    conn.commit()
    conn.close()

def save_job_session(candidate_id: int, job_title: str, company_name: str, job_input: str, company_intel: str, tailored_markdown: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO job_sessions (candidate_id, job_title, company_name, job_input, company_intelligence, tailored_resume_markdown)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (candidate_id, job_title, company_name, job_input, company_intel, tailored_markdown))
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id

def get_candidate_sessions(candidate_id: int):
    conn = get_db_connection()
    sessions = conn.execute("SELECT * FROM job_sessions WHERE candidate_id = ? ORDER BY created_at DESC", (candidate_id,)).fetchall()
    conn.close()
    return sessions