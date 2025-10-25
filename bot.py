import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import asyncio

# === 基本设定 ===
BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
ADMIN_ID = 7815801706
GROUP_ID = -1003101091433

# === 粗口 & 18禁禁词列表 ===
BANNED_WORDS = [
    # 马来语粗口
    "babi", "anjing", "pukimak", "sial", "bangang", "bodoh", "setan", "celaka",
    "puki", "kote", "jubur", "tetek", "butuh", "pantat", "burit", "bontot",

    # 英语粗口
    "fuck", "shit", "bitch", "fck", "wtf", "asshole", "idiot", "stupid", "moron", "nigga",
    "slut", "whore", "bastard", "dick", "cock", "pussy", "boobs", "cum", "anal", "fucking",

    # 中文粗口
    "操你妈", "去你妈", "他妈的", "死开", "傻逼", "狗屎", "妈的", "垃圾", "王八蛋", "贱人", "婊子",

    # 18禁 / 性暗示词
    "sex", "porn", "nude", "blowjob", "handjob", "naked", "xxx", "69", "hentai", "masturbate",
    "milf", "daddy", "boob", "vagina", "penis", "virgin", "hot girl", "make love", "fetish", "threesome",

    # emoji 粗俗类
    "🍆", "🍑", "💦", "🖕", "🖕🏻", "🖕🏽", "🖕🏿", "💋", "👅", "😈", "😏", "🔥"
]

# === 数据储存 ===
user_warnings = {}

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)


# === 欢迎新成员 ===
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        username = member.first_name
        chat_id = update.effective_chat.id
        text = (
            f"👋 Selamat datang {username}!\n\n"
            f"Untuk aktifkan akaun anda, sila jemput sekurang-kurangnya 3 kawan ke dalam group ini 🫶\n"
            f"Klik butang di bawah untuk semak status jemputan anda 👇"
        )
        button = InlineKeyboardButton("📨 Semak / Jemput Kawan", url=f"https://t.me/{context.bot.username}")
        markup = InlineKeyboardMarkup([[button]])
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


# === 违规检测 ===
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.first_name
    text = update.message.text.lower() if update.message.text else ""

    for word in BANNED_WORDS:
        if word in text:
            user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
            warn_count = user_warnings[user_id]

            # 私信警告用户
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ Amaran #{warn_count}:\nKata-kata tidak sopan / 18+ telah dikesan.\n"
                         f"Sila jaga adab anda di dalam group ini."
                )
            except:
                pass  # 有时私聊未开启，不影响执行

            # 通知管理员
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚨 Pengguna '{username}' menggunakan perkataan terlarang dalam group."
            )

            # 三次违规 → 踢出群
            if warn_count >= 3:
                try:
                    await context.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🚫 Anda telah dikeluarkan kerana melanggar peraturan lebih daripada 3 kali."
                    )
                except:
                    pass
                user_warnings.pop(user_id, None)
            break


# === 启动 Bot ===
async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    logging.info("🤖 Bot sedang beroperasi...")
    await app.run_polling()
