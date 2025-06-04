from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
import datetime
import os

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
from handlers import start, remove, user, admins, broadcast, help 
from database import add_admin, is_admin
from handlers.user import myinfo , notify_expiring_users


# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    job_queue = app.job_queue
    job_queue.run_repeating(notify_expiring_users, interval=60, first=0)

    conv_change_name = ConversationHandler(
    entry_points=[CommandHandler("change_name", change_name_start)],
    states={
        ASK_USER_CHAT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name_receive_user)],
        ASK_NEW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_name_save)],
    },
    fallbacks=[],
    )
    conv_change_duration = ConversationHandler(
    entry_points=[CommandHandler("change_duration", change_duration_start)],
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

    # Add other command handlers
    app.add_handler(CommandHandler("remove", remove.remove))
    app.add_handler(CommandHandler("users", user.list_users))
    app.add_handler(CommandHandler("add_admin", admins.add_admin_command))
    app.add_handler(CommandHandler("remove_admin", admins.remove_admin_command))
    app.add_handler(CommandHandler("list_admins", admins.list_admins_command))
    app.add_handler(CommandHandler("broadcast", broadcast.broadcast))
    app.add_handler(CommandHandler("myinfo", myinfo))
    app.add_handler(conv_change_name)
    app.add_handler(conv_change_duration)
    app.add_handler(CommandHandler("myinfo", myinfo))  # existing command
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📋 Mes Infos$"), myinfo))  # button with text






    # Start polling updates from Telegram
    app.run_polling()


if __name__ == "__main__":
    main()
