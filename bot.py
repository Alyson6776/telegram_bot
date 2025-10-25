import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
GROUP_NAME = "🧧Kaki free credit🧧"
INVITE_FILE = "invites.json"
WARN_FILE = "warnings.json"

# =========================
# LOGGING SETUP
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# =========================
# FILE HANDLERS
# =========================
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

# =========================
# BAD WORDS (Malay + English + Emoji)
# =========================
BAD_WORDS = [
    "fuck", "shit", "bitch", "asshole", "dick", "pussy", "fucker", "bastard",
    "cunt", "motherfucker", "whore", "slut", "cock", "porn", "sex", "nigger",
    "babi", "anjing", "sial", "bodoh", "bangang", "pukimak", "kote", "burit",
    "pepek", "konek", "sundal", "pelacur", "lancap", "jubo", "puki", "mak kau",
    "🍆", "💦", "🖕", "🍑", "👅", "😈", "🔞", "🤤"
]

# =========================
# AUTO WELCOME NEW USER
# =========================
async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if result.new_chat_member.status == "member":
        user = result.new_chat_member.user
        user_id = str(user.id)
        username = user.first_name or "kawan"

        if user_id not in invites:
            invites[user_id] = {"invited": []}
            save_json(INVITE_FILE, invites)

        msg = (
            f"👋 Selamat datang @{username} ke {GROUP_NAME}!\n\n"
            "Untuk aktifkan akaun kau dan claim ganjaran 🎁,\n"
            "kau perlu jemput **3 orang kawan baru** ke group ni 💌\n\n"
            "Tekan butang bawah ni untuk share group ni terus 📲"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "💌 Jemput Kawan Sekarang",
                    url=f"https://t.me/share/url?url=Join+{GROUP_NAME}+dan+dapatkan+free+credit%21",
                )
            ]
        ]

        await context.bot.send_message(
            chat_id=update.chat_member.chat.id,
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

# =========================
# ADD FRIEND MANUALLY
# =========================
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

        if len(invites[inviter]["invited"]) >= 3:
            await update.message.reply_text(
                f"🎉 Tahniah! User {inviter} dah jemput cukup 3 kawan 💪"
            )
        else:
            remain = 3 - len(invites[inviter]["invited"])
            await update.message.reply_text(
                f"✅ User {inviter} dah jemput {len(invites[inviter]['invited'])}, tinggal {remain} lagi!"
            )
    else:
        await update.message.reply_text(f"⚠️ User {invited} dah pernah dijemput oleh {inviter}.")

# =========================
# CHECK INVITES
# =========================
async def check_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    invited_count = len(invites.get(user_id, {"invited": []})["invited"])

    if invited_count >= 3:
        msg = (
            f"🔥 @{user.first_name}, mantap! Kau dah jemput cukup 3 orang 💯\n"
            "Sekarang akaun kau dah aktif sepenuhnya 🎊"
        )
    else:
        remain = 3 - invited_count
        msg = (
            f"😅 @{user.first_name}, kau baru jemput {invited_count} orang.\n"
            f"Kena jemput {remain} lagi untuk aktifkan akaun 💪"
        )

    await update.message.reply_text(msg)

# =========================
# BAD WORD FILTER
# =========================
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
                f"⚠️ @{username}, tolong jaga bahasa ya 😅 (Amaran pertama)"
            )
        elif warnings[user_id] == 2:
            await update.message.reply_text(
                f"🚨 @{username}, ni dah amaran **kedua**! Jangan guna bahasa kasar lagi 😠"
            )
        else:
            await update.message.reply_text(
                f"❌ @{username} dah diberi 3 amaran. Kau akan dikeluarkan dari group 😔"
            )
            try:
                await context.bot.ban_chat_member(update.message.chat_id, user.id)
            except Exception as e:
                print("Error removing user:", e)

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Welcome new member
    app.add_handler(ChatMemberHandler(welcome_user, ChatMemberHandler.CHAT_MEMBER))
    # Admin command
    app.add_handler(CommandHandler("addfriend", add_friend))
    app.add_handler(CommandHandler("check", check_invite))
    # Bad word filter
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_bad_words))

    print("✅ Bot sedang beroperasi tanpa henti... 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
