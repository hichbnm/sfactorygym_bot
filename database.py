import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Create the users table if it doesn't exist

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    name TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    chat_id INTEGER PRIMARY KEY,
    name TEXT
)
""")
conn.commit()

def add_user(chat_id, name):
    cursor.execute("INSERT OR REPLACE INTO users (chat_id, name) VALUES (?, ?)", (chat_id, name))
    conn.commit()

def user_exists(chat_id):
    cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (chat_id,))
    return cursor.fetchone() is not None
    
def get_user_name(chat_id):
    cursor.execute("SELECT name FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_user_name(chat_id):
    cursor.execute("SELECT name FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    return result[0] if result else None


def remove_user(chat_id):
    cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT chat_id , name  FROM users")
    return cursor.fetchall()

# Admin functions

def add_admin(chat_id, name):
    cursor.execute("INSERT OR IGNORE INTO admins (chat_id, name) VALUES (?, ?)", (chat_id, name))
    conn.commit()
def remove_admin(chat_id):
    cursor.execute("DELETE FROM admins WHERE chat_id = ?", (chat_id,))
    conn.commit()

def is_admin(chat_id):
    cursor.execute("SELECT 1 FROM admins WHERE chat_id = ?", (chat_id,))
    return cursor.fetchone() is not None

def get_all_admins():
    cursor.execute("""
        SELECT admins.chat_id, users.name 
        FROM admins
        LEFT JOIN users ON admins.chat_id = users.chat_id
    """)
    return cursor.fetchall()