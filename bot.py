import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
import os
import json

# === 从环境变量加载 ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

# === 违禁词列表（粗口 + 18禁 + 侮辱词） ===
BANNED_WORDS = [
    "bodoh", "bangang", "babi", "anjing", "pukimak", "fuck", "shit", "fck", "sial", "kote", "lancau",
    "idiot", "wtf", "dumb", "bitch", "gay", "porn", "sex", "nude", "boobs", "cock", "pussy",
    "faggot", "motherfucker", "slut", "penis", "vagina", "susu", "pantat", "konek", "ngentot",
    "blowjob", "naked", "camsex", "hentai", "gayporn", "anal", "suck", "threesome", "milf", "cum"
]

# === 数据 ===
DATA_FILE = "invites.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

logging.basicConfig(level=logging.INFO)

# === 欢迎新成员 ===
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        username = member.first_name
        user_id = member.id
        chat_id = update.effective_chat.id

        if str(user_id) not in user_data:
            user_data[str(user_id)] = {"invited": 0, "warnings": 0}
            save_data()

        text = (
            f"👋 Selamat datang {username}！\n\n"
            "Untuk mula, klik butang di bawah untuk semak cara jemput kawan 👇\n"
            "📢 Jemput sekurang-kurangnya 3 rakan untuk aktifkan akaun anda 💪"
        )

        button = InlineKeyboardButton("📎 Jemput Kawan", url="https://t.me/+YOUR_GROUP_INVITE_LINK")
        keyboard = InlineKeyboardMarkup([[button]])

        await context.bot.send_message(chat_id, text, reply_markup=keyboard)

# === 检查消息内容是否违规 ===
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text.lower()
    chat_id = update.effective_chat.id

    for word in BANNED_WORDS:
        if word in text:
            user_data[user_id]["warnings"] += 1
            save_data()
            warn_count = user_data[user_id]["warnings"]

            if warn_count < 3:
                await update.message.reply_text(
                    f"⚠️ {update.message.from_user.first_name}, mesej anda mengandungi perkataan terlarang.\n"
                    f"Amaran {warn_count}/3. Sila berhati-hati."
                )
            else:
                await update.message.reply_text("🚫 Anda telah menerima 3 amaran dan akan dikeluarkan.")
                await context.bot.ban_chat_member(chat_id, update.message.from_user.id)
                await context.bot.send_message(
                    ADMIN_ID,
                    f"❗ User {update.message.from_user.first_name} telah dibuang kerana 3 kali melanggar peraturan."
                )
            break

# === 检查邀请是否达到3个 ===
async def check_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    invited_count = user_data.get(user_id, {}).get("invited", 0)

    if invited_count >= 3:
        msg = "✅ Tahniah! Akaun anda telah diaktifkan 🎉"
    else:
        msg = f"📢 Anda telah jemput {invited_count}/3 rakan.\nJemput lagi {(3 - invited_count)} untuk aktifkan akaun anda 💪"

    await update.message.reply_text(msg)

# === 启动 Bot ===
async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    app.add_handler(CommandHandler("check", check_invites))

    await app.run_polling()
