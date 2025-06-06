# 🏋️‍♂️ Salle de Sport Bot

A Telegram bot to manage gym (salle de sport) memberships. It allows users to register, select subscription durations (1, 3, or 12 months), and check their remaining subscription time. Admins can manage users, broadcast messages, and update subscription details.

---

## 📦 Features

* 🤖 User Registration via `/start`
* ⏳ Select subscription duration: 1 month, 3 months, 12 months
* 📋 View subscription info via `/myinfo`
* 🛠 Admin-only features:

  * `/add_admin` — Add new admin
  * `/change_name` — Change a user's name
  * `/change_duration` — Modify a user's subscription period
  * `/broadcast` — Send message to all users
  * `/users` — List all registered users
  * `/admins` — List all admins

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
docker-compose build
docker-compose up
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

1. User sends `/start`
2. Bot asks for name and subscription duration
3. Saves data and confirms registration
4. Users can check their info with 📋 **Mes Infos**
5. Admin sees a different interface without the user button

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
