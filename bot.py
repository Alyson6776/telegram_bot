import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ChatMemberHandler, filters, CallbackQueryHandler, ContextTypes
import json, os, asyncio

# === ✅ 基本设定 ===
BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
GROUP_NAME = "🧧Kaki free credit🧧"
INVITES_FILE = "invites.json"

# === ✅ 初始化数据 ===
if os.path.exists(INVITES_FILE):
    with open(INVITES_FILE, "r") as f:
        invites = json.load(f)
else:
    invites = {}

def save_invites():
    with open(INVITES_FILE, "w") as f:
        json.dump(invites, f, indent=4)

# === ✅ 禁词清单（马来文 + 英文 + emoji）===
BANNED_WORDS = [
    "fuck","babi","sial","anjing","kote","puki","bangsat","bodoh",
    "stupid","wtf","idiot","sundal","fucker","🖕","🖕🏻","🖕🏼","🖕🏽","💩","🤬"
]

# === ✅ 日志设定 ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === ✅ /start 指令 ===
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
            "Untuk mula, jemput 3 orang kawan masuk ke group ni dulu 😎\n"
            "Bila cukup **3 orang**, kamu akan unlock semua feature 💥"
        )
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        message = f"🎉 Hai {username}! Kamu dah jemput **3 kawan**! Terima kasih sebab support 🙌"
        reply_markup = None

    await update.message.reply_text(message, reply_markup=reply_markup)

# === ✅ 邀请统计 ===
async def myinvites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    count = invites.get(user_id, {}).get("count", 0)
    await update.message.reply_text(f"📊 Kamu dah jemput **{count}/3** kawan setakat ni.")

# === ✅ 检测新成员进群（自动加分邀请）===
async def track_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_members = update.message.new_chat_members
    inviter_id = update.message.from_user.id
    inviter_name = f"@{update.message.from_user.username}" if update.message.from_user.username else update.message.from_user.first_name

    if not new_members:
        return

    inviter_id_str = str(inviter_id)
    if inviter_id_str not in invites:
        invites[inviter_id_str] = {"count": 0, "warned": False}

    invites[inviter_id_str]["count"] += len(new_members)
    save_invites()

    await update.message.reply_text(
        f"🎉 Terima kasih {inviter_name} kerana jemput {len(new_members)} kawan! "
        f"Jumlah terkini: **{invites[inviter_id_str]['count']}/3** ✅"
    )

# === ✅ 文字检测（禁词 + 欢迎互动）===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    text = update.message.text.lower()

    if any(word in text for word in BANNED_WORDS):
        if user_id not in invites:
            invites[user_id] = {"count": 0, "warned": False}
        if not invites[user_id]["warned"]:
            invites[user_id]["warned"] = True
            save_invites()
            await update.message.reply_text(f"⚠️ @{user_name}, tolong jaga bahasa ya. Ini amaran pertama.")
        else:
            await update.message.reply_text(f"🚫 @{user_name}, kamu dah diberi amaran. Admin akan pantau mesej kamu.")
        return

    if "hai" in text or "hello" in text:
        await update.message.reply_text(f"Halo @{user_name}! 👋 Selamat datang ke {GROUP_NAME}!")

# === ✅ 按钮动作 ===
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📨 Hantar link ni kepada 3 kawan kamu sekarang:\n"
        "👉 https://t.me/share/url?url=Join+group+ni+dan+dapat+free+rewards!"
    )

# === ✅ 机器人主程序 ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myinvites", myinvites))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_invites))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot sedang berjalan di Replit secara 24 jam...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

