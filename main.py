import asyncio
import keep_alive
from bot import run_bot

keep_alive.keep_alive()
asyncio.run(run_bot())
