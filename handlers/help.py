from telegram import Update
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = """
🤖 *Liste des commandes disponibles*:
/start - Commencer et enregistrer votre nom
/remove - Se désinscrire
/users - Voir la liste des utilisateurs (admin uniquement)
/broadcast - Envoyer un message à tous les utilisateurs (admin uniquement)
/add_admin - Ajouter un admin par ID (admin uniquement)
/admins - Voir la liste des admins
/help - Afficher ce message
    """
    await update.message.reply_text(commands, parse_mode="Markdown")
