from database.database import remove_user
from telegram import Update
from telegram.ext import ContextTypes


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_user(chat_id)
    await update.message.reply_text("You have been unsubscribed from updates.")