from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from dotenv import load_dotenv
from handlers import start, remove ,user , admins , broadcast , help
from database import add_admin, is_admin, get_all_admins
import os


# Load environment variables
load_dotenv()

# Get the bot token and admin chat ID from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))


def main():
    app = Application.builder().token(BOT_TOKEN).build()


    if not is_admin(ADMIN_CHAT_ID):
        # If the admin is not in the database, add them
        add_admin(ADMIN_CHAT_ID, "Initial Admin")

    # Conversation handler for /start
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start.start)],
        states={
            start.ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, start.save_name)]
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("remove", remove.remove))
    app.add_handler(CommandHandler("users", user.list_users))
    app.add_handler(CommandHandler("add_admin", admins.add_admin_command))
    app.add_handler(CommandHandler("remove_admin", admins.remove_admin_command))
    app.add_handler(CommandHandler("list_admins", admins.list_admins_command))
    app.add_handler(CommandHandler("broadcast", broadcast.broadcast))
    app.add_handler(CommandHandler("help", help.help_command))


    
    app.run_polling()

if __name__ == "__main__":
    main()
# This is the main entry point for the bot. It sets up the application, handlers, and starts polling for updates.