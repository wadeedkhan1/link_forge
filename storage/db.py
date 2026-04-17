import sqlite3
import os

# Path to the database file (relative to project root)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'crawler.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # lets us access columns by name (row['title'])
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT    NOT NULL,
            title       TEXT,
            text        TEXT,
            status_code INTEGER,
            depth       INTEGER DEFAULT 0,
            session_id  TEXT DEFAULT 'legacy',
            crawled_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(url, session_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url  TEXT NOT NULL,
            target_url  TEXT NOT NULL,
            session_id  TEXT DEFAULT 'legacy',
            UNIQUE(source_url, target_url, session_id)
        )
    ''')
    
    # Safely add new columns if they don't exist, without deleting data
    try:
        cursor.execute("ALTER TABLE pages ADD COLUMN images TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE pages ADD COLUMN metadata TEXT DEFAULT '{}'")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

import json

def insert_page(url, title, text, status_code, depth, session_id="legacy", images=None, metadata=None):
    if images is None: images = []
    if metadata is None: metadata = {}
    
    conn = get_connection()
    conn.execute(
        '''
        INSERT OR IGNORE INTO pages (url, title, text, status_code, depth, session_id, images, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (url, title, text, status_code, depth, session_id, json.dumps(images), json.dumps(metadata))
    )
    conn.commit()
    conn.close()



def insert_link(source_url, target_url, session_id="legacy"):
    conn = get_connection()
    conn.execute(
        '''
        INSERT OR IGNORE INTO links (source_url, target_url, session_id)
        VALUES (?, ?, ?)
        ''',
        (source_url, target_url, session_id)
    )
    conn.commit()
    conn.close()

def get_all_pages(session_id=None):
    conn = get_connection()
    if session_id:
        rows = conn.execute(
            'SELECT id, url, title, text, status_code, depth, crawled_at, session_id, images, metadata FROM pages WHERE session_id = ? ORDER BY id',
            (session_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            'SELECT id, url, title, text, status_code, depth, crawled_at, session_id, images, metadata FROM pages ORDER BY id'
        ).fetchall()
    conn.close()
    
    # Process JSON fields before returning
    results = []
    for r in rows:
        d = dict(r)
        d['images'] = json.loads(d.get('images') or '[]')
        d['metadata'] = json.loads(d.get('metadata') or '{}')
        results.append(d)
        
    return results


def search_pages(keyword, session_id=None):
    conn = get_connection()
    if session_id:
        rows = conn.execute(
            '''
            SELECT id, url, title, text, status_code, depth, crawled_at, session_id
            FROM pages
            WHERE (LOWER(title) LIKE LOWER(?) OR LOWER(text) LIKE LOWER(?)) AND session_id = ?
            ORDER BY id
            ''',
            (f'%{keyword}%', f'%{keyword}%', session_id)
        ).fetchall()
    else:
        rows = conn.execute(
            '''
            SELECT id, url, title, text, status_code, depth, crawled_at, session_id
            FROM pages
            WHERE LOWER(title) LIKE LOWER(?) OR LOWER(text) LIKE LOWER(?)
            ORDER BY id
            ''',
            (f'%{keyword}%', f'%{keyword}%')
        ).fetchall()
    conn.close()
    return rows


def get_all_links(session_id=None):
    conn = get_connection()
    if session_id:
        rows = conn.execute('SELECT source_url, target_url FROM links WHERE session_id = ?', (session_id,)).fetchall()
    else:
        rows = conn.execute('SELECT source_url, target_url FROM links').fetchall()
    conn.close()
    return rows

def get_page_count(session_id=None):
    conn = get_connection()
    if session_id:
        count = conn.execute('SELECT COUNT(*) FROM pages WHERE session_id = ?', (session_id,)).fetchone()[0]
    else:
        count = conn.execute('SELECT COUNT(*) FROM pages').fetchone()[0]
    conn.close()
    return count

def get_latest_session():
    conn = get_connection()
    row = conn.execute('SELECT session_id FROM pages ORDER BY crawled_at DESC LIMIT 1').fetchone()
    conn.close()
    return row[0] if row else None
