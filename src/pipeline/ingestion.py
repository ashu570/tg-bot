from src.libs.user_client import userbot, bot
from src.libs.logger import logger
from config import config
from src.pipeline.processing import process_files 
import re

def build_smart_regex(search_text: str) -> re.Pattern:
    if not search_text or not search_text.strip():
        return re.compile(r"^$") 
        
    # Inserts space between a character and number from the search query 
    search_text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', search_text)
    search_text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', search_text)
    
    words = search_text.split()
    escaped_words = [re.escape(w) for w in words]
    delimiter_bridge = r"[\W_]*"
    regex_string = delimiter_bridge.join(escaped_words)
    return re.compile(regex_string, re.IGNORECASE)

async def ingest_raw_files(reply_chat_id: int):
    """Userbot scans the RAW channel history for matching files."""
    logger.info("Scanning RAW channel for 'v-' files...")
    matched_messages = []

    try:
        async for msg in userbot.iter_messages(config.raw_channel, limit=100):
            if msg.media and (msg.document or msg.video):
                
                file_name = ""
                if msg.document:
                    for attr in msg.document.attributes:
                        if hasattr(attr, 'file_name'):
                            file_name = attr.file_name
                            break
                            
                caption = msg.text or ""

                if file_name.startswith("v-") or caption.startswith("v-"):
                    matched_messages.append(msg)
        
        logger.info(f"Ingestion complete. Found {len(matched_messages)} target files.")
        
        if matched_messages:
            await bot.send_message(
                reply_chat_id, 
                f"✅ **Ingestion Complete:** Found **{len(matched_messages)}** files ready for the staging phase."
            )
            await process_files(matched_messages, reply_chat_id)
        else:
            await bot.send_message(reply_chat_id, "No files starting with 'v-' were found in the recent history.")

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        await bot.send_message(reply_chat_id, f"❌ **Error during ingestion:** `{e}`")