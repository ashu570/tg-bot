import asyncio
import cryptg
import os
from config import config
from src.libs.logger import logger
from src.libs.user_client import bot, userbot
from src.helper.commons import common_helper
import src.handlers.commands

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
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
    common_helper.clean_directory(DOWNLOAD_DIR)
    asyncio.run(main())