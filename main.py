from bot import run_bot
from keep_alive import keep_alive
import asyncio

if __name__ == "__main__":
    keep_alive()
    asyncio.run(run_bot())
