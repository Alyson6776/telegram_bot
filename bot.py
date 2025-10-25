import logging
import json
import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
GROUP_NAME = "🧧Kaki free credit🧧"

INVITES_FILE   = "invites.json"     # { user_id: {"count": int, "code": "FREE10_001"} }
VIOLATIONS_FILE= "violations.json"  # { user_id: int }
BLOCKED_FILE   = "blocked.json"     # { user_id: true }
CODESEQ_FILE   = "code_seq.json"    # { "next": 1 }

# =========================
# STORAGE HELPERS
# =========================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

invites    = load_json(INVITES_FILE, {})
violations = load_json(VIOLATIONS_FILE, {})
blocked    = load_json(BLOCKED_FILE, {})
codeseq    = load_json(CODESEQ_FILE, {"next": 1})

def next_coupon() -> str:
    n = codeseq.get("next", 1)
    code = f"FREE10_{n:03d}"
    codeseq["next"] = n + 1
    save_json(CODESEQ_FILE, codeseq)
    return code

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("kaki-bot")

# =========================
# BAN WORDS (MY + EN + Emoji)
# =========================
BANNED = {
    "babi","bodoh","sial","anjing","puki","pukimak","lancau","kote","konek","cipap","bangsat","sundal",
    "fuck","shit","bitch","cunt","wtf","fucker","asshole","idiot","stupid",
    "🖕","💩","🤬"
}

# =========================
# UTIL
# =========================
def display_name(user) -> str:
    return f"@{user.username}" if user.username else user.first_name or "kawan"

def ensure_user(user_id: str):
    if user_id not in invites:
        invites[user_id] = {"count": 0}
        save_json(INVITES_FILE, invites)

# =========================
# PRIVATE MESSAGES (PM) TEMPLATES
# =========================
def invite_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💌 Jemput Kawan Sekarang", url=f"https://t.me/share/url?url=Join+{GROUP_NAME.replace(' ', '+')}+untuk+free+credit%21")],
        [InlineKeyboardButton("📊 Semak Status Jemputan", callback_data="check_status")]
    ])

# =========================
# COMMANDS
# =========================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """PM 或群里都能用；在 PM 里展示按钮。"""
    user = update.effective_user
    uid = str(user.id)
    ensure_user(uid)

    name = display_name(user)
    cnt  = invites[uid]["count"]
    if cnt >= 3:
        text = (
            f"🎉 Hai {name}!\n"
            f"Kau dah cukup **3 kawan** — akaun kau dah aktif. Terima kasih support! 🙌"
        )
        kb = None
    else:
        remain = 3 - cnt
        text = (
            f"👋 Hai {name}!\n"
            f"Untuk aktif & claim ganjaran, jemput **{remain} lagi** kawan masuk {GROUP_NAME}.\n\n"
            "Tekan butang di bawah untuk jemput / semak status."
        )
        kb = invite_keyboard()

    try:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        # 若在群里且 message 可能为 None 时兜底
        await context.bot.send_message(chat_id=user.id, text=text, reply_markup=kb, parse_mode="Markdown")

async def myinvites_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看自己的邀请进度（建议在私聊用）。"""
    user = update.effective_user
    uid = str(user.id)
    ensure_user(uid)
    cnt = invites[uid]["count"]
    text = f"📊 Status jemputan: **{cnt}/3**" if cnt < 3 else "✅ Tahniah! Kau dah cukup **3/3** 🎉"
    await update.message.reply_text(text, parse_mode="Markdown")

# =========================
# NEW MEMBERS IN GROUP
# =========================
async def new_members_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    触发点：群里出现新成员（可能由某人邀请，或自己通过链接加入）。
    - 在群里公开欢迎并提示“去私聊 bot 查看详情”
    - 私信新成员教学 + 按钮
    - 如果有人把别人拉进来（message.from_user），把该 inviter 的 count += 新成员数量
    """
    msg = update.message
    if not msg or not msg.new_chat_members:
        return

    inviter = msg.from_user            # 可能是邀请人；如果成员是自己点链接加入，inviter 就是他自己
    inviter_id = str(inviter.id)

    added = msg.new_chat_members
    # 公开欢迎每个新成员 + 引导去私聊
    for member in added:
        mention = display_name(member)
        welcome_text = (
            f"👋 Selamat datang {mention} ke {GROUP_NAME}!\n\n"
            "🎯 Untuk dapatkan ganjaran, kau perlu jemput **3 kawan**.\n"
            "💬 **PM bot sekarang** untuk lihat cara jemput & semak status jemputan kamu."
        )
        try:
            await msg.reply_text(welcome_text, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Send group welcome failed: {e}")

        # 私信该新成员（若没跟 bot 开过对话可能会失败，忽略即可）
        pm_text = (
            f"Hai {mention}! 👋\n"
            f"Untuk claim ganjaran dalam {GROUP_NAME}, jemput **3 kawan** ya.\n\n"
            "Guna butang di bawah untuk jemput / semak status."
        )
        try:
            await context.bot.send_message(chat_id=member.id, text=pm_text, reply_markup=invite_keyboard(), parse_mode="Markdown")
        except Exception as e:
            logger.info(f"PM new member failed (user not started): {e}")

    # 统计可能的邀请者（如果 A 把 B/C 加进群，from_user=A）
    try:
        if added and inviter:  # 有新增 & 有触发者
            ensure_user(inviter_id)
            invites[inviter_id]["count"] = invites[inviter_id].get("count", 0) + len(added)
            save_json(INVITES_FILE, invites)
            # 达标即发券（仅私信）
            if invites[inviter_id]["count"] >= 3 and not invites[inviter_id].get("code"):
                code = next_coupon()
                invites[inviter_id]["code"] = code
                save_json(INVITES_FILE, invites)
                try:
                    await context.bot.send_message(
                        chat_id=inviter.id,
                        text=(
                            f"🎉 Tahniah {display_name(inviter)}!\n"
                            f"Kau dah jemput **{invites[inviter_id]['count']}** kawan.\n"
                            f"🎁 Kod ganjaran kau: **{code}**\n"
                            "Gunakan kod ini ikut arahan promosi."
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.info(f"PM inviter reward failed: {e}")
            else:
                # 没达标也发进度（私信）
                try:
                    await context.bot.send_message(
                        chat_id=inviter.id,
                        text=f"✅ Jemputan berjaya! Status semasa: **{invites[inviter_id]['count']}/3**.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.info(f"PM inviter progress failed: {e}")
    except Exception as e:
        logger.warning(f"Update inviter stats failed: {e}")

# =========================
# TEXT FILTER (GROUP & PM)
# =========================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    检测禁词：
    - 每次违规都“私信用户”提醒（而不是在群里发）
    - 第3次：踢出群，并加入 blocked 列表（后续消息与私聊一律忽略）
    """
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    uid  = str(user.id)
    text = update.message.text.lower()

    # 若已被本 bot 封锁，直接忽略
    if uid in blocked:
        return

    # 仅当出现禁词才处理
    if any(bad in text for bad in BANNED):
        count = violations.get(uid, 0) + 1
        violations[uid] = count
        save_json(VIOLATIONS_FILE, violations)

        # 私信用户——可能失败（没启动私聊/拉黑 bot），容错即可
        try:
            if count == 1:
                await context.bot.send_message(
                    chat_id=user.id,
                    text="⚠️ Amaran 1/3: Tolong elakkan guna bahasa kasar dalam group. 🙏"
                )
            elif count == 2:
                await context.bot.send_message(
                    chat_id=user.id,
                    text="⚠️ Amaran 2/3: Ini amaran terakhir. Jika ulang, anda akan dikeluarkan. 🚨"
                )
            else:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=f"🚫 Anda telah melanggar peraturan 3 kali. Anda akan dikeluarkan dari {GROUP_NAME}."
                )
        except Exception as e:
            logger.info(f"PM warn failed: {e}")

        # 第3次：尝试踢出 + 本地封锁
        if count >= 3 and update.message.chat and update.message.chat.type in ("group","supergroup"):
            try:
                await context.bot.ban_chat_member(chat_id=update.message.chat_id, user_id=user.id)
            except Exception as e:
                logger.warning(f"Ban failed: {e}")
            blocked[uid] = True
            save_json(BLOCKED_FILE, blocked)
        return

    # 普通问候（可选）
    if any(greet in text for greet in ("hai","hello","hi","helo")):
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"Hai {display_name(user)}! 👋 PM bot ni untuk semak cara jemput & status jemputan.",
            )
        except Exception as e:
            logger.info(f"PM greet failed: {e}")

# =========================
# CALLBACK BUTTONS (PM)
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = str(query.from_user.id)
    ensure_user(uid)

    if query.data == "check_status":
        cnt = invites[uid]["count"]
        if cnt >= 3:
            # 发放/回显奖励码
            if not invites[uid].get("code"):
                code = next_coupon()
                invites[uid]["code"] = code
                save_json(INVITES_FILE, invites)
            code = invites[uid]["code"]
            text = f"🎉 Status: **{cnt}/3** — Dah cukup!\n🎁 Kod ganjaran anda: **{code}**"
        else:
            text = f"📊 Status jemputan: **{cnt}/3**\nTeruskan jemput kawan ya! 💪"
        await query.answer()
        await query.edit_message_text(text, parse_mode="Markdown")
    else:
        await query.answer()

# =========================
# MAIN (PTB + Flask Heartbeat)
# =========================
async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("myinvites", myinvites_cmd))

    # New members (group)
    app
