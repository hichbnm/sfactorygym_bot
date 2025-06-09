import sqlite3
from datetime import datetime, timedelta
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Create the users table if it doesn't exist

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY,
    name TEXT,
    subscription_start DATE,
    subscription_end DATE ,
    status TEXT DEFAULT 'pending'
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    chat_id INTEGER PRIMARY KEY,
    name TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question TEXT,
    answer TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS broadcasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
    sent_count INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

def save_user_history(user_id, question, answer):
    cursor.execute(
        "INSERT INTO user_history (user_id, question, answer) VALUES (?, ?, ?)",
        (user_id, question, answer)
    )
    conn.commit()

def get_user_history(user_id, limit=5):
    cursor.execute(
        "SELECT question, answer FROM user_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    return cursor.fetchall()


def get_user_info(chat_id):   
    cursor.execute("SELECT name, subscription_start, subscription_end FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()

    if result:
        name, start_str, end_str = result
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        return name, start_date, end_date
    return None

def add_user(chat_id, name, months=1):
    subscription_start = datetime.now().date()
    subscription_end = (datetime.now() + timedelta(days=30 * months)).date()
    cursor.execute("INSERT OR REPLACE INTO users (chat_id, name ,subscription_start,subscription_end, status) VALUES (?, ?, ? , ?, 'pending')", (chat_id, name, subscription_start, subscription_end))
    conn.commit()

def user_exists(chat_id):
    cursor.execute("SELECT 1 FROM users WHERE chat_id = ?", (chat_id,))
    return cursor.fetchone() is not None
    
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

def get_subscription_end(chat_id):
    cursor.execute("SELECT subscription_end FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_remaining_days(chat_id):
    cursor.execute("SELECT subscription_end FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        return None
    subscription_end = datetime.strptime(result[0], "%Y-%m-%d").date()
    today = datetime.today().date()
    delta = (subscription_end - today).days
    return delta

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

def update_user_name(chat_id, new_name):
    cursor.execute("UPDATE users SET name = ? WHERE chat_id = ?", (new_name, chat_id))
    conn.commit()

def update_user_subscription(chat_id, months):
    new_end_date = (datetime.now() + timedelta(days=30 * months)).date()
    cursor.execute("UPDATE users SET subscription_end = ? WHERE chat_id = ?", (new_end_date, chat_id))
    conn.commit()


def is_approved(chat_id):
    cursor.execute("SELECT status FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    return result and result[0] == 'approved'
def is_expired(chat_id):
    cursor.execute("SELECT status FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    return result and result[0] == 'expired'
def is_pending(chat_id):
    cursor.execute("SELECT status FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    return result and result[0] == 'pending'

def disable_expired_users():
    today = datetime.today().date()
    cursor.execute("""
        UPDATE users
        SET status = 'expired'
        WHERE status = 'approved'
        AND subscription_end <= ?
    """, (today,))
    conn.commit()
def get_expired_users():
    cursor.execute("SELECT chat_id, name FROM users WHERE status = 'expired'")
    return cursor.fetchall()

def renew_subscription(chat_id, months=1):
    subscription_start = datetime.now().date()
    subscription_end = (datetime.now() + timedelta(days=30 * months)).date()
    cursor.execute(
        "UPDATE users SET subscription_start = ?, subscription_end = ?, status = 'pending' WHERE chat_id = ?",
        (subscription_start, subscription_end, chat_id)
    )
    conn.commit()

def get_all_approved_users():
    cursor.execute("SELECT chat_id, name FROM users WHERE status = 'approved'")
    return cursor.fetchall()

def save_broadcast(message, sent_count):
    cursor.execute(
        "INSERT INTO broadcasts (message, sent_count) VALUES (?, ?)",
        (message, sent_count)
    )
    conn.commit()

def get_broadcast_count():
    cursor.execute("SELECT COUNT(*) FROM broadcasts")
    return cursor.fetchone()[0]

def get_pending_approvals_count():
    cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'pending'")
    return cursor.fetchone()[0]

def remove_user(chat_id):
    cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
    conn.commit()