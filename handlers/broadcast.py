from telegram import Update
from telegram.ext import ContextTypes
from database import get_all_users, is_admin

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    users = get_all_users()

    sent_count = 0
    for chat_id, name in users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

    await update.message.reply_text(f"✅ Message envoyé à {sent_count} utilisateurs.")
# This function allows an admin to broadcast a message to all users.