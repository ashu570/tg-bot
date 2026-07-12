from telethon import TelegramClient
from config import config

# We initialize them here, but we start them in main.py
bot = TelegramClient('bot_session', config.api_id, config.api_hash)
userbot = TelegramClient('userbot_session', config.api_id, config.api_hash)