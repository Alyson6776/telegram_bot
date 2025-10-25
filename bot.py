import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import json, os, asyncio
from flask import Flask
from threading import Thread

# === ✅ Bot Settings ===
BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
GROUP_NAME = "🧧Kaki free credit🧧"
INVITES_FILE = "invites.json"

# === ✅ Load or create data ===
if os.path.exists(INVITES_FILE):
    with open(INVITES_FILE, "r") as f:
        invites = json.load(f)
else:
    invites = {}

def save_invites():
    with open(INVITES_FILE, "w") as f:
        json.dump(invites, f, indent=4)

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
        invites[user_id] = {"count": 0, "warned": False}
        save_invites()

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
        invites[inviter_id] = {"count": 0, "warned": False}

    invites[inviter_id]["count"] += added_count
    save_invites()

    await update.message.reply_text(
        f"🎉 Terima kasih {inviter_name} kerana jemput {added_count} kawan!\n"
        f"Jumlah terkini: **{invites[inviter_id]['count']}/3** ✅"
    )

# === 💬 Message filtering & response ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user = update.effective_user
    user_id = str(user.id)
    user_name = user.first_name

    # 🔞 Detect bad words
    if any(word in text for word in BANNED_WORDS):
        if user_id not in invites:
            invites[user_id] = {"count": 0, "warned": False}
        if not invites[user_id]["warned"]:
            invites[user_id]["warned"] = True
            save_invites()
            await update.message.reply_text(f"⚠️ @{user_name}, tolong jaga bahasa kamu. Ini amaran pertama 🙏")
        else:
            await update.message.reply_text(f"🚫 @{user_name}, kamu dah diberi amaran. Admin akan pantau mesej kamu.")
        return

    # 👋 Friendly greetings
    if "hai" in text or "hello" in text:
        await update.message.reply_text(f"Halo @{user_name}! 👋 Selamat datang ke {GROUP_NAME}!")

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

# === 💓 Heartbeat (Flask server for uptime) ===
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is alive! 🟢"

def run_flask():
    app_flask.run(host='0.0.0.0', port=8080)

# === 🧩 Run everything ===
if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())


