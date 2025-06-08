from telegram import Update
from telegram import Bot
from telegram.ext import ContextTypes , ConversationHandler
from database.database import get_all_users, is_admin, get_remaining_days , get_user_info , is_approved , is_expired , is_pending , renew_subscription, get_user_name , get_all_admins , disable_expired_users
import os
import datetime
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

# Get user info command
disable_expired_users()
async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    disable_expired_users()
    

    chat_id = update.effective_chat.id
    user_info = get_user_info(chat_id)
    if is_pending(chat_id):
        await update.message.reply_text("⏳ Merci de patienter pendant que l'admin valide votre inscription.")
        return
    if  is_expired(chat_id):
        await update.message.reply_text("⚠️ Votre abonnement est expiré. Envoyez /renew pour demander un renouvellement")
        return

    if not user_info:
        await update.message.reply_text("❌ Vous n'êtes pas encore inscrit.")
        return

    name, start_date, end_date = user_info
    days_left = (end_date - start_date).days if end_date >= start_date else 0

    if days_left > 0:
        status = f" ⏳ {days_left} jours restants"
        msg = (
            f"👤 *Nom* : {name}\n"
            f"🗓️ *Début* : {start_date.strftime('%d-%m-%Y')}\n"
            f"📅 *Fin* : {end_date.strftime('%d-%m-%Y')}\n"
            f"📊 *Statut* : ✅ Actif {status}\n"
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
        elif days_left == 0:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ Bonjour {name}, votre abonnement a expiré aujourd'hui. Veuillez le renouveler pour continuer à profiter de la salle de sport."
                )
            except Exception as e:
                print(f"Erreur lors de l'envoi à {chat_id}: {e}")

async def renew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_expired(chat_id):
        await update.message.reply_text("Votre abonnement n'est pas expiré. Vous ne pouvez le renouveler que lorsqu'il est expiré.")
        return

    # Ask for duration
    reply_keyboard = [["1 mois", "3 mois", "12 mois"]]
    await update.message.reply_text(
        "Choisissez la durée de renouvellement :",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return "RENEW_DURATION"

from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def renew_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    duration_str = update.message.text
    months = 1 if "1" in duration_str else 3 if "3" in duration_str else 12

    renew_subscription(chat_id, months)
    await update.message.reply_text(
        "Votre demande de renouvellement a été envoyée à l'admin pour validation. Veuillez patienter.",
        reply_markup=ReplyKeyboardRemove()
    )

    # Notify admins with inline buttons
    name = get_user_name(chat_id)
    for admin_id, _ in get_all_admins():
        buttons = [
            [
                InlineKeyboardButton("✅ Accepter", callback_data=f"renew_approve_{chat_id}"),
                InlineKeyboardButton("❌ Refuser", callback_data=f"renew_decline_{chat_id}")
            ]
        ]
        await context.bot.send_message(
            admin_id,
            f"🔄 Demande de renouvellement d'abonnement:\n"
            f"🆔 ID: {chat_id}\n"
            f"👤 Nom: {name}\n"
            f"⏳ Durée: {months} mois",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    return ConversationHandler.END