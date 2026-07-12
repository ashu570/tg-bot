import os
import re 
import asyncio
from src.libs.logger import logger
from src.libs.user_client import bot, userbot
from config import config
from telethon import Button

LINK_BOT_USERNAME = "@Links_X_Bot"

def format_shadow_caption(original_message, new_filename):
    original_text = original_message.text or ""
    if original_text.startswith("v-"):
        original_text = original_text[2:].strip()
    description = original_text if original_text else "No additional description provided."
    return (
        f"🎬 **{new_filename}**\n\n"
        f"📝 **Description:**\n{description}\n\n"
        f"🛡 *Securely archived by Orchestrator*"
    )

async def bridge_to_link_bot(shadow_messages: list, reply_chat_id: int, batch_size: int):
    """
    Step 4 & 5: Executes the specific /batch workflow with Link_X_Bot,
    extracts the URL, and publishes to the Ready channel.
    """
    await bot.send_message(reply_chat_id, "🔗 **Stage 4: Bridging...**\nExecuting batch command with link generator...")
    
    try:
        # Open conversation with a strict 15-second timeout as requested
        async with userbot.conversation(LINK_BOT_USERNAME, timeout=30) as conv:
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
                    print(reply_text)
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
        # To be tested
        # target_entity = await userbot.get_input_entity(config.shadow_channel)
        # await bot.send_message(
        #     target_entity, 
        #     final_caption,
        #     buttons=[Button.url("📥 Access Batch", batch_link)]
        # )
        await userbot.send_message(
            config.shadow_channel,
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

async def publish_and_cleanup(processed_assets: list, reply_chat_id: int):
    await bot.send_message(
        reply_chat_id, 
        "🚀 **Stage 3: Publishing to Shadow...**\nUploading individual formatted posts to the archive."
    )
    shadow_messages = []
    try:
        # Iterate through every downloaded and renamed file
        for index, asset in enumerate(processed_assets, start=1):
            filename = os.path.basename(asset['video'])
            logger.info(f"Uploading file {index}/{len(processed_assets)} to Shadow Channel...")
            
            # Generate the rich caption utilizing the original RAW message data
            rich_caption = format_shadow_caption(asset['original_message'], filename)
            
            # Upload the video + thumbnail + rich caption to the Shadow channel
            shadow_msg = await userbot.send_file(
                config.shadow_channel,
                file=asset['video'],
                thumb=asset['thumbnail'],
                caption=rich_caption,
                supports_streaming=True
            )
            
            # Save the resulting message object (We will need this later for Step 4)
            shadow_messages.append(shadow_msg)

            # --- STRICT GARBAGE COLLECTION ---
            # Delete the local files immediately after a successful upload
            os.remove(asset['video'])
            os.remove(asset['thumbnail'])
            logger.info(f"Cleaned up local files for {filename}")

        # Report final success to you for this phase
        await bot.send_message(
            reply_chat_id, 
            f"✅ **Shadow Archive Complete!**\nSuccessfully uploaded and formatted {len(processed_assets)} files. Local disk cleared."
        )
        
        if shadow_messages :
            await bridge_to_link_bot(shadow_messages, reply_chat_id, len(processed_assets))

    except Exception as e:
        logger.exception(f"Error during Shadow publishing phase: {e}")
        await bot.send_message(reply_chat_id, f"❌ **Error during publishing:** `{e}`")