from config import config
from src.libs.user_client import userbot
import os

ASSETS_DIR = 'assets'

async def send_join_link():
    card_text = f"** Please spread the word and show your support for [TIF]😍** \n \n http://t.me/addlist/DghB-MUobDM1YWQ1 \n \n **Share with your pals and have fun!🥹**"
    await userbot.send_message(config.shadow_channel, card_text)

async def send_final_sticker():
    sticker_path = os.path.join(ASSETS_DIR, "shadow_sticker.webp")
    if os.path.exists(sticker_path):
        await userbot.send_message(config.shadow_channel, file=sticker_path)