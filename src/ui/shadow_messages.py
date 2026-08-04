from config import config
from src.libs.user_client import userbot

async def send_join_link():
    card_text = f"""
                    **Please spread the word and show your support for [TIF]😍 **
                    http://t.me/addlist/DghB-MUobDM1YWQ1 
                    **Share with your pals and have fun!🥹**
                """
    await userbot.send_message(config.shadow_channel, card_text)