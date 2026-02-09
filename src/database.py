import sqlite3
from src.config import DB_PATH

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS journalists (
        id TEXT PRIMARY KEY,
        name TEXT,
        profile_url TEXT
    )
    ''')
    
    # Ensure 'content' column exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id TEXT PRIMARY KEY,
        title TEXT,
        url TEXT,
        published_date TEXT,
        content TEXT,
        description TEXT,
        keywords TEXT,
        journalist_id TEXT,
        FOREIGN KEY (journalist_id) REFERENCES journalists (id)
    )
    ''')
    conn.commit()
    conn.close()
    
def upgrade_db_schema():
    """Adds new columns to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN description TEXT")
        print("Added column: description")
    except sqlite3.OperationalError:
        pass # Column already exists

    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN keywords TEXT")
        print("Added column: keywords")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()
    conn.close()

def save_articles(journalist_id, articles):
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    for article in articles:
        try:
            cursor.execute('''
            INSERT INTO articles (id, title, url, journalist_id)
            VALUES (?, ?, ?, ?)
            ''', (article['id'], article['name'], article['url'], journalist_id))
            count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    print(f"Saved {count} new articles to database.")

def get_articles_missing_metadata():
    """Fetches articles, that dont have body or metadata"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, url FROM articles WHERE content IS NULL OR content = '' OR description IS NULL")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "url": row[1]} for row in rows]

def update_article_full_data(article_id, content, description, keywords):
    """Updates article body and metadata"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE articles 
        SET content = ?, description = ?, keywords = ?
        WHERE id = ?
    ''', (content, description, keywords, article_id))
    conn.commit()
    conn.close()
    
def create_journalist(j_id, j_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO journalists (id, name, profile_url)
    VALUES (?, ?, ?)
    ''', (j_id, j_name, f"https://yle.fi/p/{j_id}/fi"))
    conn.commit()
    conn.close()