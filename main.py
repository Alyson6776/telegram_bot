import threading
from keep_alive import keep_alive
from bot import run_bot
import asyncio

def run_flask():
    keep_alive()

threading.Thread(target=run_flask).start()
asyncio.run(run_bot())
