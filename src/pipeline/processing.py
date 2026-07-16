import os
import re
import asyncio
from src.libs.logger import logger
from src.libs.user_client import bot
from src.pipeline.publish import publish_and_cleanup
from src.helper.commons import ACTIVE_BATCHES, common_helper
from src.helper.file_formator import format_video_metadata
from src.helper.progress_tracker import ProgressTracker
from config import config
import cryptg

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def extract_thumbnail(video_path: str, thumb_path: str):
    command = [
        "ffmpeg",
        "-ss", "00:00:05",
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        "-vf", "scale=w=320:h=320:force_original_aspect_ratio=decrease",
        thumb_path,
        "-y"
    ]
    # Run the FFmpeg command asynchronously so we don't block the bot
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await process.communicate()
    if process.returncode == 0 and os.path.exists(thumb_path):
        return thumb_path
    return None

async def process_files(messages: list, reply_chat_id: int):
    #Todo: 1 TMDB API Call per season
    """Downloads, renames, and extracts thumbnails for matching files."""
    processed_assets = []
    status_msg = await bot.send_message(
        reply_chat_id, 
        "⏳ **Stage 2: Staging...**\nInitializing downloads..."
    )
    total_messages = len(messages)
    for index, msg in enumerate(messages, start=1):
        try:
            logger.info(f"Downloading file {index}/{len(messages)}...")
            tracker = ProgressTracker(status_msg, index, total_messages, "Download")
            new_filename, final_caption = format_video_metadata(msg.file.name if msg.file else msg.text)
            custom_file_path = os.path.join(DOWNLOAD_DIR, new_filename if new_filename else '')
            original_file_path = await msg.download_media(file=custom_file_path, progress_callback = tracker )
            if not original_file_path:
                logger.warning(f"Failed to download media for message {msg.id}")
                continue
            tmdb_result = await fetch_meta_from_tmdb(common_helper.clean_file_name(msg.file.name) if msg.file else msg.text)
            file,_ = os.path.splitext(new_filename)
            thumb_filename = f"{file}.jpg"
            thumb_file_path = os.path.join(DOWNLOAD_DIR, thumb_filename)
            extracted_thumb = None
            if tmdb_result and tmdb_result.get("poster_url"):
                image_bytes = await common_helper.make_request(tmdb_result.get("poster_url"), method="GET", response_format="bytes")
                if image_bytes:
                    try:
                        with open(thumb_file_path, 'wb') as f:
                            f.write(image_bytes)
                        extracted_thumb = thumb_file_path
                    except IOError as e:
                        logger.error(f"Failed to write image to disk: {e}")
            if not extracted_thumb:
                logger.info(f"Extracting thumbnail for {new_filename}...")
                extracted_thumb = await extract_thumbnail(custom_file_path, thumb_file_path)
            # Todo: Extreme priority download and upload immediately
            # Todo: Attach a sticker once the upload is done for all the files
            processed_assets.append({
                "video": custom_file_path,
                "thumbnail": extracted_thumb,
                "original_message": msg,
                "caption": final_caption
            })
            
        except Exception as e:
            logger.exception(f"Error processing message {msg.id}: {e}")
            
    await bot.send_message(
        reply_chat_id, 
        f"✅ **Processing Complete:** Successfully staged {len(processed_assets)} files locally."
    )

    if processed_assets:
        # Todo: Needs a robust sort 
        processed_assets.sort(key=lambda x: x['caption'])
        await publish_and_cleanup(processed_assets, reply_chat_id)
    return processed_assets

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