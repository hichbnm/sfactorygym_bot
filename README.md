# S Factory Gym Bot 🤖

A Telegram bot and web dashboard for managing gym memberships and subscriptions. This system provides an automated way to handle member registrations, subscription management, and administrative tasks.

## Features 🌟

### For Members
- Easy registration process
- Subscription management
- Automatic expiration notifications
- AI-powered assistant for queries
- Subscription renewal requests
- View personal subscription information

### For Administrators
- Web dashboard for member management
- Member approval system
- Subscription duration management
- Broadcast messages to members
- Admin user management
- Member information editing
- Pending approvals management

## Tech Stack 💻

- **Backend**: Python
- **Bot Framework**: python-telegram-bot
- **Web Framework**: FastAPI
- **Database**: SQLite
- **Template Engine**: Jinja2
- **Containerization**: Docker
- **AI Integration**: OpenRouter API

## Prerequisites 📋

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- Telegram Bot Token
- OpenRouter API Key (for AI assistant feature)

## Installation 🚀

1. Clone the repository:
```bash
git clone https://github.com/yourusername/telegram-salle.git
cd telegram-salle
```

2. Create a `.env` file with the following variables:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_admin_chat_id
OPENROUTER_API_KEY=your_openrouter_api_key
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application 🏃

### Using Docker
```bash
docker-compose up -d
```

### Manual Setup
 Start the bot:
```bash
python bot.py
```


## Usage 📱

### Bot Commands

#### User Commands
- `/start` - Start and register your name
- `/myinfo` - View subscription information
- `/assistant` - Chat with AI assistant 🤖
- `/assistant_history` - View AI chat history 🧠
- `/renew` - Renew your subscription

#### Admin Commands
- `/broadcast` - Send message to all users
- `/users` - View user list
- `/change_name` - Modify user name
- `/change_duration` - Modify subscription duration
- `/add_admin` - Add admin by ID
- `/remove_admin` - Remove admin by ID
- `/list_admins` - View admin list

### Web Dashboard
Access the web dashboard at `http://localhost:8000` to:
- Manage members
- Handle pending approvals
- Send broadcast messages
- Edit member information
- Manage admin users

## Project Structure 📁

```
telegram-salle/
├── bot.py              # Main bot application
├── fastapi_app.py      # Web dashboard application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── database/          # Database related files
├── handlers/          # Bot command handlers
├── static/           # Static files for web dashboard
├── templates/        # HTML templates
└── media/           # Media files
```

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments 🙏

- python-telegram-bot team
- FastAPI team
- OpenRouter for AI capabilities
