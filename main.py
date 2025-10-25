from keep_alive import keep_alive
from bot import run_bot
import threading
import asyncio

# 启动 Flask 心跳服务（让 UptimeRobot ping）
keep_alive()

# 启动 Telegram Bot（在独立线程运行）
def start_bot():
    asyncio.run(run_bot())

t = threading.Thread(target=start_bot)
t.start()
