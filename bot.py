import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import json
import os

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
INVITE_FILE = "invites.json"
GROUP_NAME = "🧧Kaki free credit🧧"

# ==============================
# LOGGING SETUP
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================
# LOAD INVITE DATA
# ==============================
def load_invites():
    if os.path.exists(INVITE_FILE):
        with open(INVITE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_invites(data):
    with open(INVITE_FILE, "w") as f:
        json.dump(data, f, indent=4)

invites = load_invites()

# ==============================
# START COMMAND
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    user_name = user.first_name or "kawan"

    if user_id not in invites:
        invites[user_id] = {"invited": []}
        save_invites(invites)

    invited_count = len(invites[user_id]["invited"])

    if invited_count >= 3:
        text = f"✅ Hai @{user_name}! Terima kasih sebab dah jemput 3 orang kawan 🎉\n\nKau dah boleh guna semua fungsi dalam kumpulan {GROUP_NAME} 😎"
        await update.message.reply_text(text)
    else:
        remaining = 3 - invited_count
        text = (
            f"👋 Selamat datang @{user_name}!\n\n"
            f"Untuk aktifkan akaun kau dalam kumpulan {GROUP_NAME}, kau kena jemput {remaining} lagi kawan 😍\n\n"
            "Klik butang bawah ni untuk jemput 👇"
        )
        keyboard = [
            [
                InlineKeyboardButton(
                    "💌 Jemput Kawan Sekarang",
                    url=f"https://t.me/share/url?url=Join+{GROUP_NAME}+dan+dapatkan+ganjaran+menarik%21",
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)

# ==============================
# INVITE CHECKER
# ==============================
async def check_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in invites:
        invites[user_id] = {"invited": []}
        save_invites(invites)

    invited_count = len(invites[user_id]["invited"])

    if invited_count >= 3:
        text = f"🎉 @{user.first_name}, kau dah berjaya jemput 3 kawan! Terima kasih sebab support 🙌"
        await update.message.reply_text(text)
    else:
        remaining = 3 - invited_count
        text = f"😅 @{user.first_name}, kau baru jemput {invited_count} orang.\nKena jemput {remaining} lagi untuk lengkapkan misi 💪"
        keyboard = [
            [
                InlineKeyboardButton(
                    "💌 Jemput Lagi",
                    url=f"https://t.me/share/url?url=Join+{GROUP_NAME}+dan+support+komuniti+ni%21",
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup)

# ==============================
# ADD FRIEND (admin only)
# ==============================
async def add_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Guna format: /addfriend <user_id> <invited_user_id>")
        return

    inviter = context.args[0]
    invited = context.args[1]

    if inviter not in invites:
        invites[inviter] = {"invited": []}

    if invited not in invites[inviter]["invited"]:
        invites[inviter]["invited"].append(invited)
        save_invites(invites)
        await update.message.reply_text(f"✅ User {invited} dah ditambah dalam senarai jemputan {inviter}!")
    else:
        await update.message.reply_text(f"⚠️ User {invited} dah pernah dijemput oleh {inviter} sebelum ni.")

# ==============================
# MAIN
# ==============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_invite))
    app.add_handler(CommandHandler("addfriend", add_friend))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()


