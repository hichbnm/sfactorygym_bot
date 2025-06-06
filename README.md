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

### 🔧 Admin Features

- `/add_admin <chat_id>` — Add a new admin
- `/change_name <chat_id> <new_name>` — Change a user's name
- `/change_duration <chat_id> <months>` — Modify a user's subscription
- `/broadcast <message>` — Send a message to all users
- `/users` — List all users
- `/admins` — List all admins
- ✅ Inline approval or rejection of subscription requests

---

## 🚀 Getting Started

### ⚖️ Prerequisites

* Python 3.10+
* Docker & Docker Compose
* Telegram Bot Token
* MySQL or PostgreSQL database

### ⚙️ Environment Setup

Create a `.env` file at the root:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_telegram_user_id
DB_HOST=db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
```

---

## 🐳 Docker Setup

To run the bot with Docker:

```bash

docker-compose up --build
```

---

## 🧪 Development Mode

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the bot:

```bash
python bot/main.py
```

---

## 👥 User Flow

1. User starts bot via `/start`
2. Bot asks for user's name
3. User selects subscription period (1/3/12 months)
4. Request is sent to admin
5. Admin accepts or declines using inline buttons
6. If accepted:
     - User can access /myinfo, /assistant, and /assistant_history
     - User is notified and has no access to features





---

## 📂 Project Structure

```
.
├── bot/                  # Bot logic and handlers
├── database/             # DB connection and utility functions
├── media/                # Bot images/logos
├── docker/               # Docker-related files
├── docker-compose.yml
├── .env.example
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
| `/admins`          | List all admins                       |

---

## 🧐 Tech Stack

* `python-telegram-bot`
* MySQL/PostgreSQL
* Docker / Docker Compose
* Python 3.10+

---

## 🤝 Contributing

Pull requests are welcome! Feel free to open issues for improvements or bugs.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
