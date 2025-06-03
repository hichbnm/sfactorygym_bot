from telegram import Update
from telegram.ext import ContextTypes
from database import add_admin, remove_admin, is_admin, get_all_admins, get_user_name

async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    if not is_admin(user_id):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /add_admin <chat_id>")
        return

    try:
        new_admin_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("L'ID doit être un nombre.")
        return

    name = get_user_name(new_admin_id)
    if not name:
        await update.message.reply_text("❌ Cet ID n'existe pas dans la liste des utilisateurs.")
        return

    add_admin(new_admin_id)
    await update.message.reply_text(f"✅ Admin ajouté : 👤 {name} (🆔 {new_admin_id})")


async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /remove_admin <chat_id>")
        return

    try:
        remove_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("L'ID doit être un nombre.")
        return

    if remove_id == user_id:
        await update.message.reply_text("Vous ne pouvez pas vous supprimer vous-même.")
        return

    remove_admin(remove_id)
    await update.message.reply_text(f"✅ Admin retiré : {remove_id}")

async def list_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Vous n'êtes pas admin.")
        return

    admins = get_all_admins()
    if not admins:
        await update.message.reply_text("Aucun admin trouvé.")
        return

    message = "👑 Liste des admins :\n"
    for chat_id, name in admins:
        display_name = name if name else "❓ Nom inconnu"
        message += f"🆔 {chat_id} — 👤 {name}\n"
    await update.message.reply_text(message)
