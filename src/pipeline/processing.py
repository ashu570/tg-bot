import os
import asyncio
from src.libs.logger import logger
from src.libs.user_client import bot
from src.pipeline.publish import publish_and_cleanup,generate_header_text, bridge_to_link_bot
from src.helper.commons import ACTIVE_BATCHES, common_helper, CANCELLED_EVENTS
from src.helper.file_formator import format_video_metadata
from src.helper.progress_tracker import ProgressTracker, ProcessCancelledError
from config import config
import cryptg
from telethon.errors import FloodWaitError
from src.libs.user_client import bot, userbot

ASSETS_DIR = 'assets'
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def process_files(messages: list, reply_chat_id: int):
    if not messages:
        logger.info(f"No matching files found for processing.")
        return []
    CANCELLED_EVENTS[reply_chat_id] = asyncio.Event()
    def get_clean_sort_key(msg):
        raw_name = msg.file.name if msg.file else msg.text
        clean_name, _ = format_video_metadata(raw_name)
        return clean_name or ""
    
    messages.sort(key=get_clean_sort_key)
    first_msg_name = messages[0].file.name if messages[0].file else messages[0].text
    first_file_name, first_caption = format_video_metadata(first_msg_name)
    tmdb_result = await fetch_meta_from_tmdb(common_helper.clean_file_name(first_msg_name))
    header_text = generate_header_text(first_caption)
    shadow_thumb_path = os.path.join(ASSETS_DIR, f"tif_logo.jpg")
    final_thumb_path = None #For the whole series from TMDB
    status_msg = await bot.send_message(reply_chat_id, "⏳ Stage 2 & 3: Processing Pipeline...")    
    total_messages = len(messages)
    shadow_messages = []
    failed_files = []
    success_files = []
    is_cancelled = False
    shadow_header = None

    if tmdb_result and tmdb_result.get("poster_url"):
        image_bytes = await common_helper.make_request(tmdb_result.get("poster_url"), method="GET", response_format="bytes")
        if image_bytes:
            base, _ = os.path.splitext(first_file_name)
            thumb_path = os.path.join(DOWNLOAD_DIR, f"{base}.jpg")
            with open(thumb_path, 'wb') as f:
                f.write(image_bytes)
            final_thumb_path = thumb_path
    if not final_thumb_path:
        final_thumb_path = shadow_thumb_path
    for index, msg in enumerate(messages, start=1):
        raw_name = msg.file.name if msg.file else msg.text
        new_filename, final_caption = format_video_metadata(raw_name)
        custom_file_path = os.path.join(DOWNLOAD_DIR, new_filename if new_filename else '')
        try:
            tracker = ProgressTracker(status_msg, index, total_messages,reply_chat_id, "Download")
            original_file_path = await msg.download_media(file=custom_file_path, progress_callback=tracker)
            if not original_file_path:
                logger.error(f"Failed to download {new_filename}")
                failed_files.append(new_filename)
                continue
            asset = {
                "video": custom_file_path,
                "thumbnail": shadow_thumb_path,
                "caption": final_caption
            }
            if not shadow_header:
                try:
                    shadow_header = await userbot.send_message(config.shadow_channel, message=header_text)
                except FloodWaitError as e:
                    logger.warning(f"Encountered FloodWaitError in shadow channel. Sleeping for {e.seconds}s.")
                    await asyncio.sleep(e.seconds)
                    shadow_header = await userbot.send_message(config.shadow_channel, message=header_text)
            tracker = ProgressTracker(status_msg, index, total_messages,reply_chat_id, 'Upload')
            shadow_msg = await publish_and_cleanup(asset, tracker)
            if shadow_msg:
                logger.info(f"Successfully published: {new_filename}")
                success_files.append(new_filename)
                shadow_messages.append(shadow_msg)
            else:
                logger.error(f"Failed to publish: {new_filename}")
                failed_files.append(new_filename)
        except ProcessCancelledError:
            logger.info(f"Pipeline cancelation requested for {common_helper.clean_file_name(first_msg_name)}.... Exiting")
            if shadow_header and len(shadow_messages) == 0:
                try:
                    await shadow_header.delete()
                    print("Deleted orphaned header message from shadow channel.")
                except Exception as e:
                    print(f"Failed to delete orphaned header: {e}")
            is_cancelled = True
            break
        except Exception:
            logger.error(f"Unexpected error processing {new_filename} for chat_id {reply_chat_id}: {e}", exc_info=True)
            failed_files.append(new_filename)
        finally:
            if os.path.exists(custom_file_path):
                os.remove(custom_file_path)
    CANCELLED_EVENTS.pop(reply_chat_id,None)
    if is_cancelled:
        logger.info(f"Pipeline cancelled for {common_helper.clean_file_name(first_msg_name)}")
        await status_msg.edit("🛑 **Process Cancelled.")
        if final_thumb_path and final_thumb_path != shadow_thumb_path and os.path.exists(final_thumb_path):
            os.remove(final_thumb_path)
        return shadow_messages
    logger.info(f"Process complete for {common_helper.clean_file_name(first_msg_name)}. Success: {len(shadow_messages)}, Failed: {len(failed_files)}")
    if shadow_messages:
        await bridge_to_link_bot(shadow_messages, reply_chat_id, total_messages, common_helper.file_meta_extractor(success_files[0]), final_thumb_path)
    if failed_files:
        failed_text = "\n".join([f"❌ `{f}`" for f in failed_files])
        await bot.send_message(
            reply_chat_id, 
            f"✅ Processed {len(shadow_messages)} files.\n\nFailed:\n{failed_text}"
        )
    else:
        await bot.send_message(
            reply_chat_id, 
            f"✅ Archive Complete!\nSuccessfully processed and uploaded {len(shadow_messages)} files."
        )
    if final_thumb_path and os.path.exists(final_thumb_path) and final_thumb_path != shadow_thumb_path:
        os.remove(final_thumb_path)
    return shadow_messages

async def handle_series_selection(chat_id: int, target_hash: str):
    # Todo: Handle select the whole series
    session_data = ACTIVE_BATCHES.get(chat_id)
    if not session_data:
        await bot.send_message(chat_id, "⚠️ Session expired.")
        return
    messages_to_process = session_data.get(target_hash)

    if not messages_to_process:
        await bot.send_message(chat_id, "⚠️ No files found for this hash.")
        return
    await process_files(messages_to_process, chat_id)

async def fetch_meta_from_tmdb (query:str):
    url = f"{config.tmdb_base_url}/search/multi"
    params = {
        "query": query
    }
    headers = {
        "Authorization": f"Bearer {config.tmdb_api_key}",
        "accept": "application/json"
    }
    data = await common_helper.make_request(url, method="GET", response_format="json", params=params, headers = headers)
    if not data or not data.get("results"):
        return None
    result = data.get("results")
    best_match = result[0]

    #Todo: Review advanced filtering
    # best_match = None
    # max_overlap = -1 
    # target_words = set(re.findall(r'\w+', query.lower()))
    # for result in data["results"]:
    #     tmdb_title = result.get("title") or result.get("name", "")
    #     title_words = set(re.findall(r'\w+', tmdb_title.lower()))
    #     overlap = len(target_words.intersection(title_words))
        
    #     if overlap > max_overlap:
    #         max_overlap = overlap
    #         best_match = result
    #     elif overlap == max_overlap and overlap >= 0:
    #         if result.get("popularity", 0.0) > best_match.get("popularity", 0.0):
    #             best_match = result
    
    if best_match:
        poster_path = best_match.get("poster_path")
        return {
            "overview": best_match.get("overview", "No overview available."),
            "poster_url": f"{config.tmdb_base_image_url}{poster_path}" if poster_path else None,
            "title": best_match.get("title") or best_match.get("name")
        }