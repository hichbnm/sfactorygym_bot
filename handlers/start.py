from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import user_exists, add_user

ASK_NAME = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if user_exists(chat_id):
        await update.message.reply_text("Bienvenue à nouveau ! Vous êtes déjà inscrit.")
        return ConversationHandler.END
    await update.message.reply_text("Bienvenue ! Quel est votre nom ?")
    return ASK_NAME

async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    name = update.message.text
    add_user(chat_id, name)
    await update.message.reply_text(f"Merci {name}, vous êtes maintenant inscrit !")
    return ConversationHandler.END
