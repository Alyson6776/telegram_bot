
    import logging
    import json
    import os
    import asyncio
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
        ContextTypes, filters
    )

    # === CONFIG ===
    BOT_TOKEN = "7650403137:AAF5m8TXWpApivJVSwsX7tX1YkNXlB8g09A"
    DATA_FILE = "invites.json"

    # === Logging ===
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
    logger = logging.getLogger(__name__)

    # === Persistence ===
    def _load():
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {"users": {}, "invited_by": {}}  # users[user_id] -> {count, claimed, code}; invited_by[new_member_id] -> inviter_id

    def _save(d):
        with open(DATA_FILE, "w") as f:
            json.dump(d, f, indent=2)

    data = _load()

    # === Helpers ===
    def _ensure_user(u_id: str):
        if u_id not in data["users"]:
            data["users"][u_id] = {"count": 0, "claimed": False, "code": None}
            _save(data)

    def _generate_code(index: int) -> str:
        return f"FREE10_{str(index).zfill(3)}"

    # === UI ===
    def home_kb(show_invite: bool):
        rows = []
        if show_invite:
            rows.append([InlineKeyboardButton("🚀 Get My Invite Instructions", callback_data="get_invite")])
        rows.append([InlineKeyboardButton("📊 Check My Progress", callback_data="check_progress")])
        return InlineKeyboardMarkup(rows)

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        u_id = str(user.id)
        _ensure_user(u_id)
        have3 = data["users"][u_id]["count"] >= 3
        await update.message.reply_text(
            "👋 Hello! Earn a reward by inviting 3 friends into the group.
"
            "Use Telegram's 'Add members' button to add your friends.
"
            "Tap a button below to continue.",
            reply_markup=home_kb(show_invite=not have3)
        )

    async def cb_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        u_id = str(q.from_user.id)
        _ensure_user(u_id)

        if q.data == "get_invite":
            await q.edit_message_text(
                "🔗 How to invite:
"
                "1) Open the group.
"
                "2) Tap the group name → 'Add members' (or invite via link).
"
                "3) Add your friends directly.

"
                "Once 3 friends join and you were the one who added them, you'll receive a promo code automatically 🎁"
            )
            return

        if q.data == "check_progress":
            rec = data["users"][u_id]
            code = rec["code"] or "No code yet."
            await q.edit_message_text(
                f"👥 Invited friends: {rec['count']}
🎁 Your reward code: {code}"
            )
            return

    # === Group events: new members ===
    async def on_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.message
        if not msg or not msg.new_chat_members:
            return

        inviter = msg.from_user  # In 'added by' scenario, this is the adder. If self-join via link, it's the new member.
        for m in msg.new_chat_members:
            # Skip if user added themselves (join via link); we cannot attribute an inviter in that case.
            if inviter and inviter.id == m.id:
                continue

            if inviter:
                inviter_id = str(inviter.id)
                new_id = str(m.id)

                # prevent counting the same new member twice
                if new_id in data["invited_by"]:
                    continue

                _ensure_user(inviter_id)
                data["invited_by"][new_id] = inviter_id
                data["users"][inviter_id]["count"] += 1
                _save(data)

                # Public announce
                inviter_name = f"@{inviter.username}" if inviter.username else inviter.first_name
                await msg.reply_text(f"👋 Welcome {m.full_name}! Invited by {inviter_name} 🌟")

                # Reward if reached 3
                rec = data["users"][inviter_id]
                if rec["count"] >= 3 and not rec["claimed"]:
                    # generate next sequential code
                    existing = [u for u in data["users"].values() if u.get("code")]
                    code = _generate_code(len(existing) + 1)
                    rec["code"] = code
                    rec["claimed"] = True
                    _save(data)

                    try:
                        await context.bot.send_message(
                            chat_id=int(inviter_id),
                            text=f"🎉 Congrats! You invited 3 friends.
Here is your promo code: {code}"
                        )
                    except Exception as e:
                        logger.error(f"DM failed: {e}")

    # === App bootstrap ===
    def main():
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CallbackQueryHandler(cb_buttons))
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_members))

        print("✅ Bot is running. Waiting for group events...")
        app.run_polling()

    if __name__ == "__main__":
        main()
