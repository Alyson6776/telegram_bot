import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

# === 配置区 ===
BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
ADMIN_ID = 123456789  # 你自己的 Telegram ID（接收违规通知）
GROUP_ID = -100000000000  # 你的群组 ID

# === 违规词列表 ===
BANNED_WORDS = [
    "bodoh", "bangang", "babi", "anjing", "pukimak", "fuck", "shit", "fck", "sial", "kote",
    "lancau", "idiot", "wtf", "🖕", "🤬", "💩"
]

# === 字典存储用户邀请与违规记录 ===
user_warnings = {}
user_invites = {}

# === 基本日志设置 ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === 欢迎新成员 ===
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        username = member.first_name
        chat_id = update.effective_chat.id
        text = (
            f"🎉 Selamat datang {username}! 👋\n\n"
            "Untuk mula, klik butang di bawah untuk semak cara jemput kawan 🎯\n\n"
            "👉 Jemput sekurang-kurangnya 3 rakan untuk aktifkan akaun anda 💪"
        )
        button = InlineKeyboardButton("📩 Semak / Jemput Kawan", url=f"https://t.me/{context.bot.username}")
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup([[button]]))

# === 检查粗口消息 ===
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.first_name
    text = update.message.text.lower()

    for word in BANNED_WORDS:
        if word in text:
            user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
            warn_count = user_warnings[user_id]

            # 私信违规者
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ {username}, mesej anda mengandungi perkataan terlarang.\n"
                         f"Amaran #{warn_count}/3\n"
                         "Tolong elak guna bahasa kasar. 🙏"
                )
            except:
                pass

            # 通知管理员
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🚨 {username} telah guna perkataan terlarang.\n"
                         f"Jumlah amaran: {warn_count}/3"
                )
            except:
                pass

            # 超过3次自动踢出
            if warn_count >= 3:
                await context.bot.ban_chat_member(chat_id=update.message.chat_id, user_id=user_id)
                await context.bot.send_message(chat_id=update.message.chat_id, text=f"🚫 {username} telah dikeluarkan sebab melanggar peraturan 3 kali.")
                del user_warnings[user_id]
            break

# === /start 指令 ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    button = InlineKeyboardButton("📨 Jemput 3 Kawan", switch_inline_query="invite")
    text = (
        f"👋 Hai {user.first_name}!\n\n"
        "🎯 Untuk aktifkan akaun anda, jemput sekurang-kurangnya **3 rakan baru** ke dalam group.\n"
        "Selepas itu, anda boleh gunakan semua fungsi khas bot ini 💫"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[button]]), parse_mode="Markdown")

# === 启动主Bot ===
async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

    print("🤖 Bot sedang berjalan...")
    await app.run_polling()
