from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from database import update_user_name, update_user_subscription, user_exists, get_user_name
from datetime import datetime
from telegram import ReplyKeyboardMarkup

ASK_USER_CHAT_ID, ASK_NEW_NAME, ASK_NEW_DURATION = range(3)

# Check admin decorator helper
async def is_admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    from database import is_admin
    return is_admin(chat_id)

# Change user name command
async def change_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_check(update, context):
        await update.message.reply_text("❌ Vous n'êtes pas autorisé à utiliser cette commande.")
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
    await update.message.reply_text(f"Nom mis à jour avec succès pour l'utilisateur {chat_id} : {new_name}", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Change subscription duration command
async def change_duration_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin_check(update, context):
        await update.message.reply_text("❌ Vous n'êtes pas autorisé à utiliser cette commande.")
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
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
