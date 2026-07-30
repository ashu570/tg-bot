from src.libs.user_client import userbot, bot
from src.libs.logger import logger
from config import config
from src.pipeline.processing import process_files 
from src.plugin.indexer import db
from src.helper.season_extractor import segregate_and_dedupe
from src.ui.season_selection import generate_season_cards                                            
import re
import asyncio

def build_smart_regex(search_text: str) -> re.Pattern:
    if not search_text or not search_text.strip():
        return re.compile(r"^$") 
        
    # Inserts space between a character and number from the search query 
    search_text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', search_text)
    search_text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', search_text)
    
    words = search_text.split()
    escaped_words = [re.escape(w) for w in words]
    # Todo: Handle more complex files such as 24Street, I.robot
    delimiter_bridge = r"[\W_]*"
    regex_string = delimiter_bridge.join(escaped_words)
    return re.compile(regex_string, re.IGNORECASE)

async def ingest_raw_files(reply_chat_id: int, search_query: str, current_index: int = 1, total_queries: int = 1):
    logger.info(f"Starting precise local scan on RAW channel for: '{search_query}'")
    matched_messages = []
    matcher = build_smart_regex(search_query)
    try:
        all_records = db.fetch_all_records()
        matched_db_ids = []
        # Todo: Improve match logic to include the whole search query (If the query is Iron man, it should match only Iron man files not Iron Fist)
        for msg_id, file_name, caption in all_records:
            if (file_name and matcher.search(file_name)) or (caption and matcher.search(caption)):
                matched_db_ids.append(msg_id)
        if matched_db_ids:
            #Todo: Use await userbot.get_input_entity(config.raw_channel) before any fetch to resolve fresh access hashes and prevent PeerIdInvalid errors.
            db_msgs = await userbot.get_messages(config.tif_raw_channel, ids=matched_db_ids)
            matched_messages.extend([m for m in db_msgs if m is not None])
            logger.info(f"Scan complete. Found {len(matched_messages)} valid matching payloads.")
        if not matched_messages :
            #Todo: Use batching to prevent flooding and insert msg in the database so that we won't require additional sync
            async for msg in userbot.iter_messages(config.tif_raw_channel):
                if msg.media and (msg.document or msg.video):
                    file_name = ""
                    if msg.document:
                        for attr in msg.document.attributes:
                            if hasattr(attr, 'file_name'):
                                file_name = attr.file_name
                                break       
                    caption = msg.text or ""
                    has_matching_filename = bool(file_name and matcher.search(file_name))
                    has_matching_caption = bool(caption and matcher.search(caption))
                    if has_matching_filename or has_matching_caption:
                        matched_messages.append(msg)
            logger.info(f"Scan complete. Found {len(matched_messages)} valid matching payloads.")
        
        if matched_messages:
            #Todo: Add a bot message for duplicate entries
            seasons_data, duplicate_count = segregate_and_dedupe(matched_messages)
            if not seasons_data:
                await bot.send_message(reply_chat_id, f"⚠️ Found files for `{search_query}`, but could not parse metadata")
                from src.handlers.commands import advance_session # Local import to prevent circular loop
                asyncio.create_task(advance_session(reply_chat_id))
                return
            await bot.send_message(
                reply_chat_id, 
                f"✅ Found **{len(matched_messages)}** files.\n Assembling files to relevant seasons. \n {duplicate_count+" duplicates found" if duplicate_count else ""}")
            await generate_season_cards(seasons_data, reply_chat_id,current_index, total_queries, search_query)
        else:
            await bot.send_message(
                reply_chat_id, 
                f"No files matching `{search_query}` were found in the channel history."
            )
            from src.handlers.commands import advance_session
            asyncio.create_task(advance_session(reply_chat_id))

    except Exception as e:
        logger.error(f"Error during optimized ingestion execution: {e}")
        await bot.send_message(reply_chat_id, f"❌ **Error during ingestion:** `{e}`")
        from src.handlers.commands import advance_session
        asyncio.create_task(advance_session(reply_chat_id))