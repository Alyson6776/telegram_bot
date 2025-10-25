import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ====== 基本配置 ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7815801706"))
GROUP_ID = int(os.getenv("GROUP_ID", "-1003101091433"))

# ====== 启用日志 ======
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== 违规与邀请追踪 ======
user_warnings = {}
user_invites = {}

# ====== 禁词列表（粗口 + 18禁 + emoji） ======
BANNED_WORDS = [
    "anjing", "babi", "pukimak", "bodoh", "bangang", "sundal", "pelacur", "fak", "fuck", "shit", "sial", "kote",
    "idiot", "wtf", "bitch", "porn", "sex", "boobs", "nude", "naked", "pussy", "cock", "dick", "vagina", "cum",
    "blowjob", "anal", "gay", "lesbian", "xxx", "horny", "69", "18sx", "💦", "🍆", "🍑", "👅", "🔞"
]

# ====== 欢迎新成员 ======
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        username = member.first_name
        chat_id = update.effective_chat.id

        text = (
            f"👋 Selamat datang {username}!\n\n"
            f"Untuk mula, klik butang di bawah untuk semak cara jemput kawan 👇\n\n"
            f"📢 Jemput sekurang-kurangnya 3 rakan untuk aktifkan akaun anda 💪"
        )

        button = InlineKeyboardButton("📨 Jemput Kawan", url=f"https://t.me/{context.bot.username}?start=invite")
        markup = InlineKeyboardMarkup([[button]])

        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)

# ====== 检测违规 ======
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.lower()

    for word in BANNED_WORDS:
        if word in text:
            user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
            warn_count = user_warnings[user_id]

            # 通知用户
            await update.message.reply_text(f"⚠️ Amaran #{warn_count}: Tolong jangan guna perkataan tidak sopan!")

            # 通知管理员
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚨 User {update.message.from_user.first_name} (ID: {user_id}) telah guna perkataan dilarang.\n"
                     f"Amaran ke-{warn_count}."
            )

            # 超过三次 → 踢出群组
            if warn_count >= 3:
                await context.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                await context.bot.send_message(chat_id=user_id, text="🚫 Anda telah dibuang dari group kerana melanggar peraturan sebanyak 3 kali.")
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"❌ User {user_id} telah dibuang selepas 3 amaran.")
            return

# ====== 启动函数 ======
async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

    logger.info("Bot sedang berjalan...")
    await app.run_polling()
