import asyncio
from config import config
from src.libs.logger import logger
from src.libs.user_client import bot, userbot
import src.handlers.commands
import cryptg

async def main():
    logger.info("Booting up Orchestrator Bot and Userbot...")
    await bot.start(bot_token=config.bot_token)
    await userbot.start()
    logger.info("✅ Ecosystem is live! src/ module layout loaded.")
    await asyncio.gather(
        bot.run_until_disconnected(),
        userbot.run_until_disconnected()
    )
if __name__ == "__main__":
    asyncio.run(main())