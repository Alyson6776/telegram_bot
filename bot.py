import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import json, os, asyncio
from flask import Flask
from threading import Thread

# === ✅ Bot Settings ===
BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
GROUP_NAME = "🧧Kaki free credit🧧"
ADMIN_ID = 123456789  # ⚠️ Gantikan dengan Telegram ID admin kamu
INVITES_FILE = "invites.json"
VIOLATION_FILE = "violations.json"

# === ✅ Load data files ===
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

invites = load_json(INVITES_FILE)
violations = load_json(VIOLATION_FILE)

def save_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# === 🚫 Banned words (Malay + English + Emoji) ===
BANNED_WORDS = [
    "fuck","babi","sial","anjing","kote","puki","bangsat","bodoh",
    "stupid","wtf","idiot","sundal","fucker","🖕","🖕🏻","🖕🏼","🖕🏽","💩","🤬"
]

# === 🧠 Logging setup ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === 🎯 /start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = f"@{user.username}" if user.username else user.first_name

    if user_id not in invites:
        invites[user_id] = {"count": 0}
        save_json(invites, INVITES_FILE)

    if invites[user_id]["count"] < 3:
        keyboard = [[InlineKeyboardButton("📩 Jemput 3 Kawan Sekarang!", callback_data="invite_friends")]]
        message = (
            f"👋 Hai {username}!\n\n"
            f"Selamat datang ke {GROUP_NAME} 🎉\n"
            "Untuk mula, jemput **3 orang kawan** masuk ke group ni 😎\n"
            "Bila cukup, kamu akan unlock semua feature 💥"
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        message = f"🎉 Hai {username}! Kamu dah jemput **3 kawan**! Terima kasih sebab support 🙌"
        reply_markup = None

    await update.message.reply_text(message, reply_markup=reply_markup)

# === 📊 /myinvites command ===
async def myinvites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    count = invites.get(user_id, {}).get("count", 0)
    await update.message.reply_text(f"📊 Kamu dah jemput **{count}/3** kawan setakat ni.")

# === 🧍 Track invited members ===
async def track_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.new_chat_members:
        return

    inviter = update.message.from_user
    inviter_id = str(inviter.id)
    inviter_name = f"@{inviter.username}" if inviter.username else inviter.first_name
    added_count = len(update.message.new_chat_members)

    if inviter_id not in invites:
        invites[inviter_id] = {"count": 0}

    invites[inviter_id]["count"] += added_count
    save_json(invites, INVITES_FILE)

    await update.message.reply_text(
        f"🎉 Terima kasih {inviter_name} kerana jemput {added_count} kawan!\n"
        f"Jumlah terkini: **{invites[inviter_id]['count']}/3** ✅"
    )

# === 💬 Handle all messages (filter + monitor) ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user = update.effective_user
    user_id = str(user.id)
    user_name = f"@{user.username}" if user.username else user.first_name

    # 🔞 Detect banned words
    if any(word in text for word in BANNED_WORDS):
        count = violations.get(user_id, 0) + 1
        violations[user_id] = count
        save_json(violations, VIOLATION_FILE)

        # Send warning privately
        try:
            if count == 1:
                await context.bot.send_message(chat_id=user.id, text=f"⚠️ {user_name}, tolong jaga bahasa kamu. Ini amaran pertama 🙏")
            elif count == 2:
                await context.bot.send_message(chat_id=user.id, text=f"⚠️ {user_name}, ini amaran kedua. Ulang lagi, kamu akan dikeluarkan 🚨")
            elif count >= 3:
                await context.bot.send_message(chat_id=user.id, text=f"🚫 {user_name}, kamu telah melanggar peraturan 3 kali. Kamu akan dikeluarkan daripada {GROUP_NAME}.")
                await context.bot.ban_chat_member(chat_id=update.message.chat_id, user_id=user.id)

                # Notify admin privately
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🚨 {user_name} (ID: {user.id}) telah dikeluarkan dari {GROUP_NAME} kerana melanggar peraturan 3 kali."
                )
        except Exception as e:
            logging.warning(f"Gagal hantar mesej: {e}")
        return

# === 📩 Button handler ===
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📨 Hantar link ni kepada 3 kawan kamu sekarang:\n"
        "👉 https://t.me/share/url?url=Join+group+ni+dan+dapat+free+rewards!"
    )

# === 🚀 Main bot ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myinvites", myinvites))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_invites))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot sedang berjalan di Replit 24 jam...")
    await app.run_polling()

# === 💓 Heartbeat for 24/7 uptime ===
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is alive! 🟢"

def run_flask():
    app_flask.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())
