import os
import re 
import asyncio
from src.libs.logger import logger
from src.libs.user_client import bot, userbot
from config import config
from telethon import Button
from src.helper.file_formator import format_video_metadata
from src.helper.commons import common_helper
from telethon.errors import FloodWaitError
from telethon.tl.types import DocumentAttributeVideo
from src.helper.progress_tracker import ProgressTracker

LINK_BOT_USERNAME = "@Links_X_Bot"

async def bridge_to_link_bot(shadow_messages: list, reply_chat_id: int, batch_size: int):
    """
    Step 4 & 5: Executes the specific /batch workflow with Link_X_Bot,
    extracts the URL, and publishes to the Ready channel.
    """
    await bot.send_message(reply_chat_id, "🔗 **Stage 4: Bridging...**\nExecuting batch command with link generator...")
    
    try:
        async with userbot.conversation(LINK_BOT_USERNAME, timeout=30) as conv:
            if batch_size == 1:
                await conv.send_message("/genlink")
                await asyncio.sleep(0.5) 
                await userbot.forward_messages(LINK_BOT_USERNAME, shadow_messages[0])
            else:   
                await conv.send_message("/batch")
                await asyncio.sleep(0.5) 
                await userbot.forward_messages(LINK_BOT_USERNAME, shadow_messages[0])
                await asyncio.sleep(0.5)
                await userbot.forward_messages(LINK_BOT_USERNAME, shadow_messages[-1])
            batch_link = None
            timeout_counter = 0
            
            while timeout_counter < 30:
                history = await userbot.get_messages(LINK_BOT_USERNAME, limit=1)
                if history:
                    latest_msg = history[0]
                    reply_text = latest_msg.raw_text or "" 
                    link_match = re.search(r'(https://t\.me/\S+\?start=\S+)', reply_text)
                    if link_match:
                        batch_link = link_match.group(1)
                        break                 
                if batch_link:
                    break
                await asyncio.sleep(1)
                timeout_counter += 1
            if not batch_link:
                raise asyncio.TimeoutError("The link was never found in the bot's messages.")
        await bot.send_message(reply_chat_id, "📢 **Stage 5: Finalizing...**\nPublishing to Ready channel.")
        final_caption = (
            "🎬 **New Video Batch Ready!**\n\n"
            f"📦 **Total Files in Batch:** {batch_size}\n\n"
            "Tap the button below to securely access your files."
            f"📥 **Access Batch:** {batch_link}"
        )
        # Todo: To be tested
        # target_entity = await userbot.get_input_entity(config.shadow_channel)
        # await bot.send_message(
        #     target_entity, 
        #     final_caption,
        #     buttons=[Button.url("📥 Access Batch", batch_link)]
        # )
        await userbot.send_message(
            config.ready_channel,
            final_caption
        )
        await bot.send_message(
            reply_chat_id, 
            f"🎉 **Pipeline Complete!**\nSuccessfully processed and published a batch of {batch_size} files."
        )

    except asyncio.TimeoutError:
        logger.error("Timed out waiting for the final link from the bot.")
        await bot.send_message(reply_chat_id, "❌ **Error:** The link generator bot did not provide a link within 15 seconds.")
    except Exception as e:
        logger.exception(f"Error during bridging phase: {e}")
        await bot.send_message(reply_chat_id, f"❌ **Error during bridging:** `{e}`")

async def publish_and_cleanup(asset: dict, tracker):
    success = False
    attempts = 0
    max_attempts = 3
    shadow_msg = None
    while not success and attempts < max_attempts:
        try:
            shadow_msg = await userbot.send_file(
                config.shadow_channel,
                file=asset['video'],
                thumb=asset['thumbnail'],
                caption=asset['caption'],
                attributes=[DocumentAttributeVideo(
                    duration=0, w=150, h=170, supports_streaming=False
                )],
                progress_callback=tracker
            )
            success = True
            await asyncio.sleep(2)
        except FloodWaitError as e:
            attempts += 1
            await asyncio.sleep(e.seconds)
        except Exception:
            break

    return shadow_msg

# For shadow header before upload
def generate_header_text(file_name: str) -> str:
    meta = common_helper.file_meta_extractor(file_name)
    title = meta.get('title', 'Unknown Title').title()
    year = meta.get('year')
    season = meta.get('season', '')
    quality = meta.get('quality', '')
    language = meta.get('language', '')
    year_str = f" ({year})" if year else ""
    header = (
        f"🎬 **{title}{year_str}**\n"
        f"📁 **Season:** {season}\n"
        f"📺 **Quality:** {quality}\n"
        f"🔊 **Language:** {language}"
    )
    return header