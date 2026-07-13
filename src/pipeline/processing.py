import os
import asyncio
from src.libs.logger import logger
from src.libs.user_client import bot
from src.pipeline.publish import publish_and_cleanup
from src.helper.commons import ACTIVE_BATCHES
from src.helper.file_formator import format_video_metadata

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
    """Downloads, renames, and extracts thumbnails for matching files."""
    processed_assets = []
    await bot.send_message(reply_chat_id, "⏳ **Stage 2: Staging...**\nDownloading and processing files. This may take a moment.")
    for index, msg in enumerate(messages, start=1):
        try:
            logger.info(f"Downloading file {index}/{len(messages)}...")
            original_file_path = await msg.download_media(file=DOWNLOAD_DIR)
            if not original_file_path:
                logger.warning(f"Failed to download media for message {msg.id}")
                continue
            file_name = os.path.basename(original_file_path)
            new_filename, final_caption = format_video_metadata(file_name) #e.g: movie.name.xxx.mp4
            new_file_path = os.path.join(DOWNLOAD_DIR, new_filename)
            os.rename(original_file_path, new_file_path)
            
            # 3. Thumbnail Extraction
            file,_ = os.path.splitext(new_filename)
            thumb_filename = f"{file}.jpg"
            thumb_file_path = os.path.join(DOWNLOAD_DIR, thumb_filename)
            
            logger.info(f"Extracting thumbnail for {new_filename}...")
            extracted_thumb = await extract_thumbnail(new_file_path, thumb_file_path)
            
            # 4. Package the assets for Phase 3 (Publishing)
            processed_assets.append({
                "video": new_file_path,
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
        await publish_and_cleanup(processed_assets, reply_chat_id)
    
    # Future hand-off to publishing.py goes here
    return processed_assets

async def handle_series_selection(chat_id: int, target_hash: str):
    session_data = ACTIVE_BATCHES.get(chat_id)
    if not session_data:
        await bot.send_message(chat_id, "⚠️ Session expired.")
        return
    messages_to_process = session_data.get(target_hash)

    if not messages_to_process:
        await bot.send_message(chat_id, "⚠️ No files found for this hash.")
        return
    await process_files(messages_to_process, chat_id)