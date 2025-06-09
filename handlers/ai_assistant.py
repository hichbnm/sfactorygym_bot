import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from database.database import (
    save_user_history,
    get_user_history,
    is_approved,
    is_expired,
    is_pending,
    disable_expired_users,
    is_admin,
)

load_dotenv()

ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# -------------------- ASSISTANT COMMAND --------------------
async def assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    disable_expired_users()
    chat_id = update.message.chat_id

    if is_expired(chat_id):
        await update.message.reply_text("⚠️ Votre abonnement est expiré. Envoyez /renew pour demander un renouvellement.")
        return

    if not is_approved(chat_id) and chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⏳ Merci de patienter pendant que l'admin valide votre inscription.")
        return

    context.user_data["assistant_mode"] = True

    if is_admin(chat_id):
        await update.message.reply_text("⛔️ Cette fonctionnalité est réservée aux utilisateurs.")
    else:
        await update.message.reply_text("Welcome to S-factory Bot! Ask me anything 🤖")

# -------------------- OPENROUTER CALL --------------------
def ask_openrouter(user_id, user_input):
    chat_id = user_id

    if not OPENROUTER_API_KEY and is_approved(chat_id):
        return "API key is missing. Please check your environment setup."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant that remembers previous conversations with the user and answers accordingly."}
    ]

    if is_approved(chat_id):
        history_items = get_user_history(user_id)[-10:]  # last 10 entries only
        for question, answer in history_items:
            messages.append({"role": "user", "content": question})
            messages.append({"role": "assistant", "content": answer})

    messages.append({"role": "user", "content": user_input})

    data = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": messages
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']
        return reply.strip()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return "❌ Unauthorized: Please verify your OpenRouter API key."
        return f"❌ HTTP Error: {e}"
    except Exception as e:
        return f"❌ Unexpected Error: {str(e)}"

# -------------------- HANDLE LONG MESSAGE REPLY --------------------
async def send_long_message(bot, chat_id, text):
    for i in range(0, len(text), 4096):
        await bot.send_message(chat_id, text[i:i + 4096])

# -------------------- GENERAL MESSAGE HANDLER --------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    user_input = update.message.text

    if not is_approved(chat_id) and chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Accès refusé. Veuillez attendre la validation de votre abonnement.")
        return

    await update.message.chat.send_action(action=ChatAction.TYPING)

    reply = ask_openrouter(user_id, user_input)

    await update.message.reply_text(reply)

    save_user_history(user_id, user_input, reply)

# -------------------- ASSISTANT MODE MESSAGE HANDLER --------------------
async def assistant_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("assistant_mode"):
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        user_input = update.message.text

        if not is_approved(chat_id):
            await update.message.reply_text("⛔ Accès refusé. Veuillez attendre la validation de votre abonnement.")
            return

        await update.message.chat.send_action(action=ChatAction.TYPING)
        reply = ask_openrouter(user_id, user_input)
        await update.message.reply_text(reply)
        save_user_history(user_id, user_input, reply)

# -------------------- HISTORY COMMAND --------------------
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    disable_expired_users()
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if is_pending(chat_id):
        await update.message.reply_text("⏳ Merci de patienter pendant que l'admin valide votre inscription.")
        return
    if is_expired(chat_id):
        await update.message.reply_text("⚠️ Votre abonnement est expiré. Envoyez /renew pour demander un renouvellement.")
        return
    if not is_approved(chat_id) and chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Accès refusé. Veuillez attendre la validation de votre abonnement.")
        return

    history_items = get_user_history(user_id)

    if not history_items:
        await update.message.reply_text("Vous n'avez pas encore d'historique 🧠")
        return

    history_text = "🧠 Your past messages:\n\n"
    for question, answer in reversed(history_items):
        history_text += f"Q: {question}\nA: {answer}\n\n"

    await send_long_message(context.bot, chat_id, history_text)

# -------------------- STOP ASSISTANT --------------------
async def stop_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["assistant_mode"] = False
    await update.message.reply_text("Assistant désactivé. Tapez /assistant pour recommencer.")
