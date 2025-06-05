from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from database import add_user, user_exists , is_admin , get_all_admins
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta

import os

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
ASK_NAME, ASK_DURATION = range(2)
CHANGE_NAME_USER, CHANGE_NAME_NEW = range(2)
CHANGE_DURATION_USER, CHANGE_DURATION_NEW = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    with open("media/sfactory.jpg", "rb") as photo:
        await context.bot.send_photo(chat_id=chat_id, photo=photo)

    # Check if user is admin
    if chat_id == ADMIN_CHAT_ID:
        await update.message.reply_text(
            " Bienvenue Admin ! "
        )
        await update.message.reply_text(
            "   Voici les commandes disponibles :\n"
            "   /broadcast - Envoyer un message à tous les utilisateurs \n"
            "   /users - Voir la liste des utilisateurs \n"
            "   /change_name - Changer le nom d'un utilisateur\n"
            "   /change_duration - Changer la durée d'abonnement d'un utilisateur\n"
            "   /list_admins - Lister les admins\n"
            "   /add_admin <chat_id> - Ajouter un admin\n" 
            "   /remove_admin <chat_id> - Retirer un admin\n"           
        )
        return ConversationHandler.END

    # If user exists
    if user_exists(chat_id):
        reply_keyboard = [["📋 Mes Infos","🤖 Assistant AI","🧠 Historique AI" ]]

        await update.message.reply_text("Vous êtes déjà inscrit.")
        await update.message.reply_text(
            "   Voici les commandes disponibles :\n"
            "   /myinfo - Voir vos informations d’abonnement \n"
            "   /assistant - Parler avec l'assistant IA 🤖 \n"
            "   /assistant_history - Voir l’historique de vos discussions IA 🧠\n" ,

            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
        )
        return ConversationHandler.END

    # New user registration
    await update.message.reply_text("Bienvenue ! Quel est votre nom ?")
    return ASK_NAME 
async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    context.user_data["name"] = update.message.text
    reply_keyboard = [["1 mois", "3 mois", "12 mois"]]
    await update.message.reply_text(
        "Choisissez la durée de votre abonnement :",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ASK_DURATION

async def save_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    duration_str = update.message.text
    months = 1 if "1 mois" in duration_str else 3 if "3 mois" in duration_str else 12

    name = context.user_data["name"]
    chat_id = update.message.chat_id

    # Save with "pending" status
    add_user(chat_id, name, months)

    await update.message.reply_text("📨 Votre demande a été envoyée à l'admin pour validation. Veuillez patienter.")

    # Notify all admins
    for admin_id, _ in get_all_admins():
        buttons = [
            [
                InlineKeyboardButton("✅ Accepter", callback_data=f"approve_{chat_id}"),
                InlineKeyboardButton("❌ Refuser", callback_data=f"decline_{chat_id}")
            ]
        ]
        await context.bot.send_message(
            admin_id,
            f"👤 Nouvelle demande d'abonnement:\n"
            f"🆔 ID: {chat_id}\n"
            f"👤 Nom: {name}\n"
            f"⏳ Durée: {months} mois",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    return ConversationHandler.END


async def change_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return ConversationHandler.END
    await update.message.reply_text("Entrez l'ID (chat_id) de l'utilisateur dont vous voulez changer le nom :")
    return CHANGE_NAME_USER


async def change_name_receive_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_str = update.message.text.strip()
    if not chat_id_str.isdigit() or not user_exists(int(chat_id_str)):
        await update.message.reply_text("ID invalide ou utilisateur non trouvé. Veuillez réessayer.")
        return CHANGE_NAME_USER
    context.user_data["target_chat_id"] = int(chat_id_str)
    await update.message.reply_text("Entrez le nouveau nom de l'utilisateur :")
    return CHANGE_NAME_NEW



async def change_duration_receive_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_str = update.message.text.strip()
    if not chat_id_str.isdigit() or not user_exists(int(chat_id_str)):
        await update.message.reply_text("ID invalide ou utilisateur non trouvé. Veuillez réessayer.")
        return CHANGE_DURATION_USER
    context.user_data["target_chat_id"] = int(chat_id_str)
    
    reply_keyboard = [["1 mois", "3 mois", "12 mois"]]
    await update.message.reply_text(
        "Choisissez la nouvelle durée d'abonnement :",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHANGE_DURATION_NEW


async def change_duration_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    duration_str = update.message.text
    months = 1 if "1" in duration_str else 3 if "3" in duration_str else 12
    chat_id = context.user_data["target_chat_id"]
    
    # fetch current name
    from database import get_user_name
    name = get_user_name(chat_id)
    if not name:
        await update.message.reply_text("Utilisateur non trouvé.")
        return ConversationHandler.END
    
    add_user(chat_id, name, months)
    
    await update.message.reply_text(
        f"Durée d'abonnement de l'utilisateur {chat_id} mise à jour à {months} mois.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END