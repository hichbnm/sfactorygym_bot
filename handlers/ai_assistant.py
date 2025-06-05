import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from database import save_user_history, get_user_history , is_approved

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Dictionary to track user history
user_history = {}

async def assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not is_approved(chat_id):
        await update.message.reply_text("⛔ Accès refusé. Veuillez attendre la validation de votre abonnement.")
        return

    await update.message.reply_text("Welcome to S-factory Bot! Ask me anything 🤖")

def ask_openrouter(user_id, user_input):
    if not OPENROUTER_API_KEY:
        return "API key is missing. Please check your environment setup."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Build user-specific chat history
    messages = []

    if user_id in user_history:
        for item in user_history[user_id]:
            messages.append({"role": "user", "content": item["question"]})
            messages.append({"role": "assistant", "content": item["answer"]})

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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_input = update.message.text

    # Show typing action
    await update.message.chat.send_action(action=ChatAction.TYPING)

    # Ask OpenRouter with history
    reply = ask_openrouter(user_id, user_input)

    # Reply to the user
    await update.message.reply_text(reply)

    save_user_history(user_id, user_input, reply)

    # Save user input and bot reply to history
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append({
        "question": user_input,
        "answer": reply
    })

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    history_items = get_user_history(user_id)
    chat_id = update.message.chat_id
    if not is_approved(chat_id):
        await update.message.reply_text("⛔ Accès refusé. Veuillez attendre la validation de votre abonnement.")
        return

    if not history_items:
        await update.message.reply_text("Vous n'avez pas encore d'historique 🧠")
        return

    history_text = "🧠 Your past messages:\n\n"
    for question, answer in reversed(history_items):
        history_text += f"Q: {question}\nA: {answer}\n\n"

    await update.message.reply_text(history_text)



