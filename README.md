# 🏋️‍♂️ Salle de Sport Bot

A Telegram bot to manage gym (salle de sport) memberships. It allows users to register, select subscription durations (1, 3, or 12 months), and check their remaining subscription time. Admins can manage users, broadcast messages, and update subscription details.

---

## 📦 Features

### 👤 User Features

- `/start` — Begin registration
- ⏳ Choose subscription duration: 1, 3, or 12 months
- 🔐 Wait for **admin approval** to access features
- 📋 `/myinfo` — View your subscription details
- 🤖 `/assistant` — Talk with the AI assistant
- 🧠 `/assistant_history` — View your AI chat history
- 🔄 `/renew` — Renew your subscription
- ⚠️ Automatic notifications for expiring subscriptions
- 🛑 Automatic deactivation of expired subscriptions

### 🔧 Admin Features

- `/add_admin <chat_id>` — Add a new admin
- `/change_name <chat_id> <new_name>` — Change a user's name
- `/change_duration <chat_id> <months>` — Modify a user's subscription
- `/broadcast <message>` — Send a message to all users
- `/users` — List all users
- `/admins` — List all admins
- ✅ Inline approval or rejection of subscription requests

- 🌐 Web Dashboard Interface:
  - User management
  - Admin management
  - Broadcast messages
  - View pending approvals
  - View broadcast statistics
  - Secure admin login

### 🤖 AI Assistant Features

- Natural language conversation
- Context-aware responses
- Chat history tracking
- `/stop` command to end conversation
- Persistent chat history per user

---

## 🚀 Getting Started

### ⚖️ Prerequisites

* Python 3.10+
* Docker & Docker Compose
* Telegram Bot Token
* SQLite database (included)

### ⚙️ Environment Setup

Create a `.env` file at the root:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_telegram_user_id
OPENROUTER_API_KEY=your_openrouter_api_key
```

---

## 🐳 Docker Setup

To run the bot with Docker:

```bash
docker-compose up --build -d
```

The web dashboard will be available at `http://localhost:5001`

---

## 🧪 Development Mode

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the bot:

```bash
python bot.py
```

The web dashboard will be available at `http://localhost:5001`

---

## 👥 User Flow

1. User starts bot via `/start`
2. Bot asks for user's name
3. User selects subscription period (1/3/12 months)
4. Request is sent to admin
5. Admin accepts or declines using inline buttons
6. If accepted:
   - User can access /myinfo, /assistant, and /assistant_history
   - User is notified and has access to features
7. Before expiration:
   - User receives notification
   - Can use /renew to extend subscription
8. After expiration:
   - Account is automatically deactivated
   - User must renew to regain access

---

## 📂 Project Structure

```
.
├── bot.py              # Main bot logic
├── flask_api.py        # Web dashboard API
├── database/           # Database operations
├── handlers/           # Command handlers
├── templates/          # Web dashboard templates
├── static/            # Web dashboard assets
├── media/             # Bot images/logos
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🛡 Admin Command Reference

| Command            | Description                           |
| ------------------ | ------------------------------------- |
| `/add_admin`       | Add a new admin by chat ID            |
| `/change_name`     | Update a user's name                  |
| `/change_duration` | Modify a user's subscription duration |
| `/broadcast`       | Send a message to all users           |
| `/users`           | List all users                        |
| `/list_admins`     | List all admins                       |

---

## 🌐 Web Dashboard Features

- **Login System**
  - Secure admin authentication
  - Session management
  - Logout functionality

- **Dashboard Overview**
  - Total users count
  - Pending approvals
  - Broadcast statistics
  - Admin list

- **User Management**
  - View all users
  - Remove users
  - View subscription status

- **Admin Management**
  - Add new admins
  - Remove existing admins
  - View admin list

- **Broadcast System**
  - Send messages to all users
  - Track broadcast success
  - View broadcast history

---

## 🧐 Tech Stack

* `python-telegram-bot`
* Flask (Web Dashboard)
* SQLite
* Docker / Docker Compose
* Python 3.10+
* APScheduler (for automated tasks)

---

## 🤝 Contributing

Pull requests are welcome! Feel free to open issues for improvements or bugs.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
