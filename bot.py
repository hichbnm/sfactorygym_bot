from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.ext import CallbackQueryHandler
from handlers.admin_edit import handle_approval
from dotenv import load_dotenv
from datetime import time
import os
from threading import Thread

from handlers.admin_edit import (
    change_name_start,
    change_name_receive_user,
    change_name_save,
    change_duration_start,
    change_duration_receive_user,
    change_duration_save,
    ASK_USER_CHAT_ID,
    ASK_NEW_NAME,
    ASK_NEW_DURATION,
)
from handlers import start, remove, user, admins, broadcast, ai_assistant
from database.database import add_admin, is_admin, get_all_admins
from flask_api import run_flask  # Import the Flask API

from handlers.user import myinfo, notify_expiring_users, renew, renew_duration
from handlers.start import disable_expired_users
from apscheduler.schedulers.background import BackgroundScheduler
from handlers.admin_edit import handle_renewal_approval
from telegram import BotCommand

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

USER_COMMANDS = [
    BotCommand("start", "Commencer et enregistrer votre nom"),
    BotCommand("myinfo", "Voir vos informations d’abonnement"),
    BotCommand("assistant", "Parler avec l'assistant IA 🤖"),
    BotCommand("assistant_history", "Voir l’historique de vos discussions IA 🧠"),
    BotCommand("renew", "Renouveler votre abonnement"),
]

ADMIN_COMMANDS = [
    BotCommand("start", "Commencer le bot "),
    BotCommand("broadcast", "Envoyer un message à tous les utilisateurs"),
    BotCommand("users", "Voir la liste des utilisateurs"),
    BotCommand("change_name", "Modifier le nom d’un utilisateur"),
    BotCommand("change_duration", "Modifier la durée d’abonnement d’un utilisateur"),
    BotCommand("add_admin", "Ajouter un admin par ID"),
    BotCommand("remove_admin", "Retirer un admin par ID"),
    BotCommand("list_admins", "Voir la liste des admins"),
]

async def set_commands(app):
    await app.bot.set_my_commands(USER_COMMANDS)
    for admin_id, _ in get_all_admins():
        await app.bot.set_my_commands(ADMIN_COMMANDS, scope={"type": "chat", "chat_id": admin_id})

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.post_init = set_commands
    scheduler = BackgroundScheduler()
    scheduler.add_job(disable_expired_users, 'interval', days=1)
    scheduler.start()

    job_queue = app.job_queue
    job_queue.run_daily(
        notify_expiring_users,
        time=time(hour=9, minute=0),  # runs every day at 09:00
        name="expiry_notification_daily"
    )

    conv_change_name = ConversationHandler(
        entry_points=[
            CommandHandler("change_name", change_name_start),
            MessageHandler(filters.Text("✏️ Changer Nom"), change_name_start),
        ],
        states={
            ASK_USER_CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name_receive_user)],
            ASK_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name_save)],
        },
        fallbacks=[],
    )
    conv_change_duration = ConversationHandler(
        entry_points=[
            CommandHandler("change_duration", change_duration_start),
            MessageHandler(filters.Text("⏳ Changer Durée"), change_name_start),
        ],
        states={
            ASK_USER_CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_duration_receive_user)],
            ASK_NEW_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_duration_save)],
        },
        fallbacks=[],
    )

    # Ensure admin is in database
    if not is_admin(ADMIN_CHAT_ID):
        add_admin(ADMIN_CHAT_ID, "Initial Admin")

    # Conversation handler for /start command
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start.start)],
        states={
            start.ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, start.save_name)],
            start.ASK_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, start.save_duration)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)
    conv_renew = ConversationHandler(
        entry_points=[
            CommandHandler("renew", renew),
            MessageHandler(filters.Text("🔄 Renouveler"), renew),
        ],
        states={
            "RENEW_DURATION": [MessageHandler(filters.TEXT & ~filters.COMMAND, renew_duration)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_renew)

    # Add other command handlers
    app.add_handler(CommandHandler("remove", remove.remove))
    app.add_handler(CommandHandler("users", user.list_users))
    app.add_handler(MessageHandler(filters.Text("👥 Liste Utilisateurs"), user.list_users))

    app.add_handler(CommandHandler("add_admin", admins.add_admin_command))
    app.add_handler(CommandHandler("remove_admin", admins.remove_admin_command))
    app.add_handler(CommandHandler("list_admins", admins.list_admins_command))
    app.add_handler(MessageHandler(filters.Text("👑 Liste Admins"), admins.list_admins_command))

    app.add_handler(CommandHandler("broadcast", broadcast.broadcast))
    app.add_handler(conv_change_name)
    app.add_handler(conv_change_duration)
    app.add_handler(CommandHandler("myinfo", myinfo))  # existing command
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📋 Mes Infos$"), myinfo))  # button with text
    app.add_handler(CommandHandler("assistant", ai_assistant.assistant))  # /assistant command
    app.add_handler(CommandHandler("assistant_history", ai_assistant.history))  # /history command
    app.add_handler(CommandHandler("history", ai_assistant.history))  # /history command

    app.add_handler(MessageHandler(filters.Text("🤖 Assistant AI"), ai_assistant.assistant))
    app.add_handler(MessageHandler(filters.Text("🧠 Historique AI"), ai_assistant.history))
    app.add_handler(CallbackQueryHandler(handle_approval, pattern="^(approve|decline)_"))
    app.add_handler(CallbackQueryHandler(handle_renewal_approval, pattern="^renew_(approve|decline)_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_assistant.assistant_message))
    app.add_handler(CommandHandler("stop", ai_assistant.stop_assistant))

    # --- Start Flask API for broadcast ---
    Thread(target=run_flask, daemon=True).start()
    # --- End Flask API for broadcast ---

    # Start polling updates from Telegram
    app.run_polling()

if __name__ == "__main__":
    main()
