import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import os

BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
GROUP_ID = -1001234567890  # Replace with your group ID

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

INVITE_FILE = "invites.json"

# Load invite data
def load_invites():
    if os.path.exists(INVITE_FILE):
        with open(INVITE_FILE, "r") as f:
            return json.load(f)
    return {}

# Save invite data
def save_invites(data):
    with open(INVITE_FILE, "w") as f:
        json.dump(data, f)

invites = load_invites()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    user_id = str(user.id)
    if user_id not in invites:
        invites[user_id] = {"invited": 0}
        save_invites(invites)

    text = (
        "👋 Welcome!\n\n"
        "To get started, please invite **3 friends** to this group.\n"
        "Once you have done so, you’ll unlock full access!"
    )
    keyboard = [[InlineKeyboardButton("📩 Invite Friends", url=f"https://t.me/share/url?url=Join+our+group!&text=Check+out+this+amazing+group!")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)

async def check_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    count = invites.get(user_id, {}).get("invited", 0)

    if count >= 3:
        await update.message.reply_text("✅ You have already invited 3 or more friends. You’re good to go!")
    else:
        await update.message.reply_text(f"👥 You’ve invited {count}/3 friends. Invite more to unlock access!")

async def add_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /addinvite <user_id>")
        return

    user_id = context.args[0]
    if user_id not in invites:
        invites[user_id] = {"invited": 1}
    else:
        invites[user_id]["invited"] += 1
    save_invites(invites)

    await update.message.reply_text(f"✅ Added 1 invite to user {user_id}. Total: {invites[user_id]['invited']}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling update:", exc_info=context.error)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_invites))
    app.add_handler(CommandHandler("addinvite", add_invite))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()

