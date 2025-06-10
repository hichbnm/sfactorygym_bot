from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from database.database import update_user_name, update_user_subscription, user_exists, get_user_name
from datetime import datetime
from telegram import ReplyKeyboardMarkup
import sqlite3
import asyncio # Import asyncio

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
ASK_USER_CHAT_ID, ASK_NEW_NAME, ASK_NEW_DURATION = range(3)
admin_reply_keyboard = [
    ["👥 Liste Utilisateurs", "👑 Liste Admins"],
    ["✏️ Changer Nom", "⏳ Changer Durée"],
]

# User Reply Keyboard Definition (for messages to users)
USER_REPLY_KEYBOARD = [
    ["📋 Mes Infos", "🤖 Assistant AI"],
    ["🧠 Historique AI", "🔄 Renouveler"]
]
USER_MARKUP = ReplyKeyboardMarkup(USER_REPLY_KEYBOARD, resize_keyboard=True)

# Helper function to send approval/decline messages to user
async def _send_user_status_notification(chat_id: int, bot, action: str):
    if action == "approve":
        with open("media/sfactory.jpg", "rb") as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo)
        await bot.send_message(chat_id, "✅ Votre abonnement a été validé. Bienvenue !")
        await bot.send_message(
            chat_id,
            "   Voici les commandes disponibles :\n"
            "   /myinfo - Voir vos informations d'abonnement \n"
            "   /assistant - Parler avec l'assistant IA 🤖 \n"
            "   /assistant_history - Voir l'historique de vos discussions IA 🧠\n"
            "   /renew - Renouveler votre abonnement 🔄\n",
            reply_markup=USER_MARKUP
        )
    elif action == "decline":
        await bot.send_message(chat_id, "❌ Votre demande d'abonnement a été refusée.")
    elif action == "renew_approve": # For renewal approval
        with open("media/sfactory.jpg", "rb") as photo:
            await bot.send_photo(chat_id=chat_id, photo=photo)
        await bot.send_message(chat_id, "✅ Votre renouvellement d'abonnement a été validé. Bienvenue à nouveau !")
        await bot.send_message(
            chat_id,
            "   Voici les commandes disponibles :\n"
            "   /myinfo - Voir vos informations d'abonnement \n"
            "   /assistant - Parler avec l'assistant IA 🤖 \n"
            "   /assistant_history - Voir l'historique de vos discussions IA 🧠\n"
            "   /renew - Renouveler votre abonnement 🔄\n",
            reply_markup=USER_MARKUP
        )
    elif action == "renew_decline": # For renewal decline
        await bot.send_message(chat_id, "❌ Votre demande de renouvellement a été refusée.")

# Check admin decorator helper
async def is_admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    from database.database import is_admin
    return is_admin(chat_id)

# Change user name command
async def change_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_check(update, context):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return ConversationHandler.END

    await update.message.reply_text("Entrez l'ID du chat Telegram de l'utilisateur dont vous voulez changer le nom :")
    return ASK_USER_CHAT_ID

async def change_name_receive_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_str = update.message.text
    if not chat_id_str.isdigit():
        await update.message.reply_text("ID invalide. Veuillez entrer un ID numérique.")
        return ASK_USER_CHAT_ID

    chat_id = int(chat_id_str)
    if not user_exists(chat_id):
        await update.message.reply_text("Utilisateur non trouvé. Essayez encore :")
        return ASK_USER_CHAT_ID

    context.user_data["edit_chat_id"] = chat_id
    current_name = get_user_name(chat_id)
    await update.message.reply_text(f"Nom actuel: {current_name}\nEntrez le nouveau nom :")
    return ASK_NEW_NAME

async def change_name_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = update.message.text
    chat_id = context.user_data.get("edit_chat_id")
    update_user_name(chat_id, new_name)
    await update.message.reply_text(
        f"Nom mis à jour avec succès pour l'utilisateur {chat_id} : {new_name}",
        reply_markup=ReplyKeyboardMarkup(admin_reply_keyboard, resize_keyboard=True)
    )
    return ConversationHandler.END

# Change subscription duration command
async def change_duration_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_check(update, context):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return ConversationHandler.END

    await update.message.reply_text("Entrez l'ID du chat Telegram de l'utilisateur dont vous voulez changer la durée de l'abonnement :")
    return ASK_USER_CHAT_ID

async def change_duration_receive_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_str = update.message.text
    if not chat_id_str.isdigit():
        await update.message.reply_text("ID invalide. Veuillez entrer un ID numérique.")
        return ASK_USER_CHAT_ID

    chat_id = int(chat_id_str)
    if not user_exists(chat_id):
        await update.message.reply_text("Utilisateur non trouvé. Essayez encore :")
        return ASK_USER_CHAT_ID

    context.user_data["edit_chat_id"] = chat_id

    reply_keyboard = [["1 mois", "3 mois", "12 mois"]]
    await update.message.reply_text(
        "Choisissez la nouvelle durée de l'abonnement :",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ASK_NEW_DURATION

from telegram import ReplyKeyboardRemove

async def change_duration_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    duration_text = update.message.text

    if "1 mois" in duration_text:
        months = 1
    elif "3 mois" in duration_text:
        months = 3
    elif "12 mois" in duration_text:
        months = 12
    else:
        await update.message.reply_text("Choix invalide. Sélectionnez 1 mois, 3 mois ou 12 mois.")
        return ASK_NEW_DURATION

    chat_id = context.user_data.get("edit_chat_id")
    update_user_subscription(chat_id, months)

    await update.message.reply_text(
        f"✅ Durée d'abonnement mise à jour : {months} mois.",
        reply_markup=ReplyKeyboardMarkup(admin_reply_keyboard, resize_keyboard=True)
    )
    return ConversationHandler.END

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = int(data.split("_")[1])
    action = data.split("_")[0]

    if action == "approve":
        cursor.execute("UPDATE users SET status = 'approved' WHERE chat_id = ?", (chat_id,))
        conn.commit()
        await _send_user_status_notification(chat_id, context.bot, "approve")
        await query.edit_message_text("✅ Utilisateur approuvé.")
    else:
        cursor.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
        conn.commit()
        await _send_user_status_notification(chat_id, context.bot, "decline")
        await query.edit_message_text("❌ Demande refusée.")

from telegram.ext import CallbackQueryHandler
from database.database import update_user_subscription

async def handle_renewal_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    action_prefix = parts[0] # e.g., 'renew'
    action = parts[1] # e.g., 'approve' or 'decline'
    chat_id = int(parts[2])

    if action == "approve":
        cursor.execute("UPDATE users SET status = 'approved' WHERE chat_id = ?", (chat_id,))
        conn.commit()
        await _send_user_status_notification(chat_id, context.bot, "renew_approve")
        await query.edit_message_text("✅ Renouvellement approuvé.")
    elif action == "decline":
        cursor.execute("UPDATE users SET status = 'expired' WHERE chat_id = ?", (chat_id,))
        conn.commit()
        await _send_user_status_notification(chat_id, context.bot, "renew_decline")
        await query.edit_message_text("❌ Renouvellement refusé.")