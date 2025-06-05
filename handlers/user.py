from telegram import Update
from telegram import Bot
from telegram.ext import ContextTypes
from database import get_all_users, is_admin, get_remaining_days , get_user_info , is_approved
import os

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

# Get user info command

async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_info = get_user_info(chat_id)
    if not is_approved(chat_id):
        await update.message.reply_text("⛔ Vous n'êtes pas approuvé pour utiliser cette commande.")
        return

    if not user_info:
        await update.message.reply_text("❌ Vous n'êtes pas encore inscrit.")
        return

    name, start_date, end_date = user_info
    days_left = (end_date - start_date).days if end_date >= start_date else 0

    if days_left > 0:
        status = f"✅ Actif — ⏳ {days_left} jours restants"
    else:
        status = "⚠️ Expiré"

    msg = (
        f"👤 *Nom* : {name}\n"
        f"🗓️ *Début* : {start_date.strftime('%d-%m-%Y')}\n"
        f"📅 *Fin* : {end_date.strftime('%d-%m-%Y')}\n"
        f"{status}"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")

# List all users for admin

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return
    # Get all users from the database

    users = get_all_users()
    if not users:
        await update.message.reply_text("Aucun utilisateur inscrit.")
        return

    message = "📋 Liste des utilisateurs :\n\n"
    for chat_id, name in users:
        if chat_id == ADMIN_CHAT_ID:
            continue

        # Get remaining days for each user
        days_left = get_remaining_days(chat_id)
        
        if days_left is None:
            status = "❌ Aucun abonnement"
        elif days_left > 0:
            status = f"✅ Actif — ⏳ {days_left} jours restants"
        else:
            status = "⚠️ Expiré"

        message += f"🆔 {chat_id} — 👤 {name} — {status}\n"

    await update.message.reply_text(message)


# Notify users whose subscription is expiring in 3 days

async def notify_expiring_users(context):
    bot: Bot = context.bot
    users = get_all_users()

    for chat_id, name in users:
        days_left = get_remaining_days(chat_id)
        if days_left == 3:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"👋 Bonjour {name}, votre abonnement expire dans 3 jours. Pensez à le renouveler pour continuer à profiter de la salle de sport 🏋️‍♂️."
                )
            except Exception as e:
                print(f"Erreur lors de l'envoi à {chat_id}: {e}")