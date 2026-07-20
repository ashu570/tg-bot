import os
import asyncio
from src.libs.logger import logger
from src.libs.user_client import bot
from src.pipeline.publish import publish_and_cleanup,generate_header_text, bridge_to_link_bot, generate_final_message
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

async def prepare_series_metadata(first_msg):
    first_msg_name = first_msg.file.name if first_msg.file else first_msg.text
    first_file_name, _ = format_video_metadata(first_msg_name)
    shadow_thumb_path = os.path.join(ASSETS_DIR, f"tif_logo.jpg")
    final_thumb_path = None
    
    tmdb_result = await fetch_meta_from_tmdb(common_helper.clean_file_name(first_msg_name))
    if tmdb_result and tmdb_result.get("poster_url"):
        image_bytes = await common_helper.make_request(tmdb_result.get("poster_url"), method="GET", response_format="bytes")
        if image_bytes:
            base, _ = os.path.splitext(first_file_name)
            thumb_path = os.path.join(DOWNLOAD_DIR, f"{base}.jpg")
            with open(thumb_path, 'wb') as f:
                f.write(image_bytes)
            final_thumb_path = thumb_path
            
    return first_file_name, final_thumb_path, shadow_thumb_path

async def execute_single_batch(messages, batch_index, total_batches, reply_chat_id, status_msg, shadow_thumb_path, header_text):
    total_messages = len(messages)
    shadow_messages = []
    shadow_header = None
    is_cancelled = False

    for index, msg in enumerate(messages, start=1):
        raw_name = msg.file.name if msg.file else msg.text
        new_filename, final_caption = format_video_metadata(raw_name)
        custom_file_path = os.path.join(DOWNLOAD_DIR, new_filename if new_filename else '')
        try:
            tracker = ProgressTracker(status_msg, index, total_messages, reply_chat_id, "Download")
            original_file_path = await msg.download_media(file=custom_file_path, progress_callback=tracker)   
            if not original_file_path:
                logger.error(f"Failed to download {new_filename}")
                continue
            asset = {"video": custom_file_path, "thumbnail": shadow_thumb_path, "caption": final_caption}
            if not shadow_header:
                try:
                    shadow_header = await userbot.send_message(config.shadow_channel, message=header_text)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                    shadow_header = await userbot.send_message(config.shadow_channel, message=header_text)   
            tracker = ProgressTracker(status_msg, index, total_messages, reply_chat_id, "Upload")
            shadow_msg = await publish_and_cleanup(asset, tracker)
            if shadow_msg:
                shadow_messages.append(shadow_msg)       
        except ProcessCancelledError:
            logger.info(f"Pipeline cancelation requested while excuting batch-{batch_index+1} .... Exiting")
            if shadow_header and len(shadow_messages) == 0:
                try:
                    await shadow_header.delete()
                    print("Deleted orphaned header message from shadow channel.")
                except Exception as e:
                    print(f"Failed to delete orphaned header: {e}")
            is_cancelled = True
            break
        except Exception as e:
            logger.error(f"Unexpected error processing {new_filename} for chat_id {reply_chat_id}: {e}", exc_info=True)
        finally:
            if os.path.exists(custom_file_path):
                os.remove(custom_file_path)   
    return shadow_messages, is_cancelled

async def process_files(batches: list, reply_chat_id: int):
    if not batches:
        return []
    CANCELLED_EVENTS[reply_chat_id] = asyncio.Event()
    first_msg = batches[0][0]
    first_file_name, final_thumb_path, shadow_thumb_path = await prepare_series_metadata(first_msg)
    status_msg = await bot.send_message(reply_chat_id, f"⏳ Processing {len(batches)} Batch(es)...")
    successful_links = {}
    is_cancelled = False
    for batch_index, messages in enumerate(batches, start=1):
        if is_cancelled:
            break  
        messages.sort(key=lambda msg: format_video_metadata(msg.file.name if msg.file else msg.text)[0] or "")
        batch_first_file = messages[0].file.name if messages[0].file else messages[0].text
        batch_meta = common_helper.file_meta_extractor(batch_first_file)
        quality_key = f"{batch_meta.get('quality', 'Unknown')}-{', '.join(batch_meta.get('custom_audio', []))}".strip()
        header_text = generate_header_text(format_video_metadata(batch_first_file)[1])
        shadow_messages, is_cancelled = await execute_single_batch(
            messages, batch_index, len(batches), reply_chat_id, status_msg, shadow_thumb_path, header_text
        )  
        if not is_cancelled and shadow_messages:
            batch_link = await bridge_to_link_bot(shadow_messages, reply_chat_id, len(shadow_messages), batch_index, len(batches))
            if batch_link:
                successful_links[quality_key] = batch_link
    CANCELLED_EVENTS.pop(reply_chat_id, None)
    if is_cancelled:
        await status_msg.edit("🛑 **Process Cancelled.**")
    elif successful_links:
        series_meta = common_helper.file_meta_extractor(first_file_name)
        final_caption = generate_final_message(series_meta, successful_links)
        await userbot.send_message(
            config.ready_channel, final_caption, 
            file=final_thumb_path if final_thumb_path and os.path.exists(final_thumb_path) else shadow_thumb_path
        )
        await bot.send_message(reply_chat_id, f"✅ Archive Complete!\nBroadcasted {len(successful_links)} quality tiers.")
    else:
        await bot.send_message(reply_chat_id, "❌ **Archive Failed:** No successful batches were bridged.")

    if final_thumb_path and final_thumb_path != shadow_thumb_path and os.path.exists(final_thumb_path):
        os.remove(final_thumb_path)

async def handle_series_selection(chat_id: int, target_hash: str):
    if chat_id not in ACTIVE_BATCHES or target_hash not in ACTIVE_BATCHES[chat_id]:
        logger.error(f"Session expired or data not found for chat {chat_id}.")
        return
    stored_value = ACTIVE_BATCHES[chat_id][target_hash]
    batches_to_process = []
    if isinstance(stored_value, str):
        child_hashes = stored_value.split("#")
        for c_hash in child_hashes:
            if c_hash in ACTIVE_BATCHES[chat_id]:
                episode_list = ACTIVE_BATCHES[chat_id][c_hash]
                if episode_list:
                    batches_to_process.append(episode_list)
    elif isinstance(stored_value, list):
        batches_to_process.append(stored_value)
    try:
        await process_files(batches_to_process, chat_id)
    except Exception as e:
        logger.error(f"Error handling batch handoff execution for chat {chat_id}: {e}", exc_info=True)
