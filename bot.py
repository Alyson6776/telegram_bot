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
WARN_FILE = "warnings.json"
GROUP_NAME = "🧧Kaki free credit🧧"

# ==============================
# LOGGING SETUP
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================
# DATA LOADERS
# ==============================
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

invites = load_json(INVITE_FILE)
warnings = load_json(WARN_FILE)

# ==============================
# BAD WORDS & EMOJI LIST
# ==============================
BAD_WORDS = [
    # English
    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "fucker", "bastard",
    "cunt", "motherfucker", "whore", "slut", "cock", "porn", "sex", "nigger",
    # Malay
    "babi", "anjing", "sial", "bodoh", "bangang", "pukimak", "kote", "burit",
    "pepek", "konek", "sundal", "pelacur", "lancap", "jubo", "puki", "mak kau",
    # Emoji-based
    "🍆", "💦", "🖕", "🍑", "👅", "😈", "🔞", "🤤"
]

# ==============================
# WELCOME NEW USER
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.first_name or "kawan"

    if user_id not in invites:
        invites[user_id] = {"invited": []}
        save_json(INVITE_FILE, invites)

    invited_count = len(invites[user_id]["invited"])

    if invited_count >= 3:
        msg = (
            f"✅ Hai @{username}! Kau memang legend 🔥\n"
            f"Kau dah jemput 3 orang kawan masuk {GROUP_NAME} 🎉\n"
            "Sekarang kau boleh enjoy semua content tanpa limit 💪"
        )
        await update.message.reply_text(msg)
    else:
        remain = 3 - invited_count
        msg = (
            f"👋 Selamat datang @{username}!\n\n"
            f"Untuk aktifkan akaun kau dalam {GROUP_NAME}, kau perlu jemput **{remain} lagi kawan** 💌\n"
            "Senang je — tekan butang bawah ni untuk terus share group ni ke Telegram 📲"
        )
        keyboard = [
            [
                InlineKeyboardButton(
                    "💌 Jemput Kawan Sekarang",
                    url=f"https://t.me/share/url?url=Join+{GROUP_NAME}+dan+dapatkan+free+credit%21",
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(msg, reply_markup=reply_markup)

# ==============================
# ADD FRIEND (for admin)
# ==============================
async def add_friend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Format salah: /addfriend <user_id> <invited_user_id>")
        return

    inviter = context.args[0]
    invited = context.args[1]

    if inviter not in invites:
        invites[inviter] = {"invited": []}

    if invited not in invites[inviter]["invited"]:
        invites[inviter]["invited"].append(invited)
        save_json(INVITE_FILE, invites)
        await update.message.reply_text(f"✅ User {invited} dah masuk senarai jemputan {inviter} 💪")
    else:
        await update.message.reply_text(f"⚠️ User {invited} dah pernah dijemput oleh {inviter} sebelum ni.")

# ==============================
# BAD WORD FILTER
# ==============================
async def filter_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.lower()

    if any(bad in text for bad in BAD_WORDS):
        user_id = str(user.id)
        username = user.first_name or "user"

        warnings[user_id] = warnings.get(user_id, 0) + 1
        save_json(WARN_FILE, warnings)

        if warnings[user_id] == 1:
            await update.message.reply_text(
                f"⚠️ @{username}, tolong jaga bahasa sikit ya 😅 (Amaran pertama)"
            )
        elif warnings[user_id] == 2:
            await update.message.reply_text(
                f"🚨 @{username}, ni amaran **kedua**! Jangan guna bahasa kasar lagi 😠"
            )
        else:
            await update.message.reply_text(
                f"❌ @{username} dah diberi 3 amaran. Kau akan dikeluarkan dari group 😔"
            )
            try:
                await context.bot.ban_chat_member(update.message.chat_id, user.id)
            except Exception as e:
                print("Error removing user:", e)

# ==============================
# CHECK INVITE STATUS
# ==============================
async def check_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    invited_count = len(invites.get(user_id, {"invited": []})["invited"])

    if invited_count >= 3:
        msg = (
            f"🎉 @{user.first_name}, mantap bro! Kau dah jemput 3 orang 💯\n"
            "Sekarang kau bebas dalam group ni 🔥"
        )
    else:
        remain = 3 - invited_count
        msg = (
            f"😅 @{user.first_name}, kau baru jemput {invited_count} orang.\n"
            f"Kena jemput {remain} lagi untuk cukup 3 💪"
        )

    await update.message.reply_text(msg)

# ==============================
# MAIN FUNCTION
# ==============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addfriend", add_friend))
    app.add_handler(CommandHandler("check", check_invite))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_bad_words))

    print("✅ Bot sedang beroperasi 24 jam tanpa henti...")
    app.run_polling()

if __name__ == "__main__":
    main()
