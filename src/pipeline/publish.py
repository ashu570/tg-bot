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
from src.helper.progress_tracker import ProgressTracker, ProcessCancelledError

LINK_BOT_USERNAME = "@Links_X_Bot"

async def bridge_to_link_bot(shadow_messages: list, reply_chat_id: int, batch_size: int, batch_index: int, total_batches: int) -> str:
    await bot.send_message(reply_chat_id, f"🔗 **Stage 4: Bridging (Batch {batch_index}/{total_batches})...**\nExecuting command with link generator...")
    batch_link = None
    try:
        async with userbot.conversation(LINK_BOT_USERNAME, timeout=60) as conv:
            if batch_size == 1:
                await conv.send_message("/genlink")
                await conv.get_response(timeout=15) 
                await userbot.forward_messages(LINK_BOT_USERNAME, shadow_messages[0])
            else:   
                await conv.send_message("/batch")
                await conv.get_response(timeout=15) 
                await userbot.forward_messages(LINK_BOT_USERNAME, shadow_messages[0])
                await conv.get_response(timeout=15) 
                await userbot.forward_messages(LINK_BOT_USERNAME, shadow_messages[-1])
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
        return batch_link
        # Todo: To be tested
        # target_entity = await userbot.get_input_entity(config.shadow_channel)
        # await bot.send_message(
        #     target_entity, 
        #     final_caption,
        #     buttons=[Button.url("📥 Access Batch", batch_link)]
        # )

    except asyncio.TimeoutError:
        logger.error("Timed out waiting for the final link from the bot.")
        await bot.send_message(reply_chat_id, "❌ **Error:** The link generator bot did not provide a link within 30 seconds.")
    except Exception as e:
        logger.exception(f"Error during bridging phase: {e}")
        await bot.send_message(reply_chat_id, f"❌ **Error during bridging:** `{e}`")

async def generate_native_link(shadow_messages: list, reply_chat_id: int, batch_size: int, batch_index: int, total_batches: int) -> str:
    await bot.send_message(
        reply_chat_id, 
        f"🔗 **Stage 4: Generating Link (Batch {batch_index}/{total_batches})...**"
    )
    try:
        if not shadow_messages:
            raise ValueError("No messages provided to generate a link.")
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        channel_id_abs = abs(config.shadow_channel)
        if len(shadow_messages) == 1:
            msg_id = shadow_messages[0].id
            payload_string = f"get-{msg_id * channel_id_abs}"
        else:
            first_msg_id = shadow_messages[0].id
            last_msg_id = shadow_messages[-1].id
            payload_string = f"get-{first_msg_id * channel_id_abs}-{last_msg_id * channel_id_abs}"
        base64_payload = common_helper.encode_payload(payload_string)
        batch_link = f"https://t.me/{bot_username}?start={base64_payload}"
        return batch_link

    except Exception as e:
        logger.exception(f"Error generating native link: {e}")
        await bot.send_message(reply_chat_id, f"❌ **Error during link generation:** `{e}`")
        return None

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
                force_document=True,
                progress_callback=tracker
            )
            success = True
            await asyncio.sleep(2)
        except ProcessCancelledError:
            logger.info(f"Upload interrupted by user cancellation for: {asset.get('video')}")
            raise
        except FloodWaitError as e:
            logger.warning(f"FloodWaitError during upload. Sleeping for {e.seconds}s.")
            attempts += 1
            await asyncio.sleep(e.seconds)
        except Exception:
            logger.error(f"Unexpected error during upload: {e}", exc_info=True)
            break

    return shadow_msg

# For shadow header before upload
def generate_header_text(file_name: str) -> str:
    meta = common_helper.file_meta_extractor(file_name)
    title = meta.get('title', 'Unknown Title').title()
    year = meta.get('year')
    season = meta.get('season', '')
    quality = meta.get('quality', '')
    language = meta.get('custom_audio', [])
    year_str = f" ({year})" if year else ""
    header = (
        f"🎬 **{title}{year_str}**\n"
        f"📁 **Season:** {season}\n"
        f"📺 **Quality:** {quality}\n"
        f"🔊 **Language:** {", ".join(language)}"
    )
    return header

def generate_final_message(metadata: dict, successful_links: dict) -> str:
    title = metadata.get("title", "UNKNOWN TITLE").upper()
    year = metadata.get("year", "")
    season = metadata.get("season", "1")
    sub = metadata.get("custom_subs", "[]")
    year_str = f" • {year}" if year else ""
    caption = (
        f"🎭 {title}{year_str}\n"
        f"📁 SEASON - {season}\n"
        f"💬 SUBTITLES - {'👍' if len(sub) > 0 and sub != '[]' else '👎'}\n"
        f"\n"
        f"📦 **AVAILABLE QUALITIES:**\n"
    )
    for quality_label, link in successful_links.items():
        formatted_label = quality_label.strip().upper()
        caption += f"🔗 **[{formatted_label}]({link})**\n"
    caption += (
        f"\n"
        f"༄༅──────────────༅༄\n"
        f"@TIFDiscuss 🌹 @TIF_WebSeries"
    )
    return caption