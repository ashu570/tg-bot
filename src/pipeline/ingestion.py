from src.libs.user_client import userbot, bot
from src.libs.logger import logger
from config import config
from src.pipeline.processing import process_files 
from src.plugin.indexer import db
from src.helper.season_extractor import segregate_and_dedupe
from src.ui.season_selection import generate_season_cards
import re

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

async def ingest_raw_files(reply_chat_id: int, search_query: str):
    logger.info(f"Starting precise local scan on RAW channel for: '{search_query}'")
    matched_messages = []
    matcher = build_smart_regex(search_query)
    try:
        all_records = db.fetch_all_records()
        matched_db_ids = []
        for msg_id, file_name, caption in all_records:
            if (file_name and matcher.search(file_name)) or (caption and matcher.search(caption)):
                matched_db_ids.append(msg_id)

        # Find messages from ids
        if matched_db_ids:
            #Todo: Use await userbot.get_input_entity(config.raw_channel) before any fetch to resolve fresh access hashes and prevent PeerIdInvalid errors.
            db_msgs = await userbot.get_messages(config.raw_channel, ids=matched_db_ids)
            matched_messages.extend([m for m in db_msgs if m is not None])
            logger.info(f"Scan complete. Found {len(matched_messages)} valid matching payloads.")
        if not matched_messages :
            #Todo: Use batching to prevent flooding and insert msg in the database so that we won't require additional sync
            async for msg in userbot.iter_messages(config.raw_channel):
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
            await bot.send_message(
                reply_chat_id, 
                f"Found **{len(matched_messages)}** files matching `{search_query}`."
            )
            seasons_data = segregate_and_dedupe(matched_messages)
            if not seasons_data:
                await bot.send_message(reply_chat_id, "⚠️ Found files, but could not parse valid Season/Episode metadata.")
                return

            await bot.send_message(
                reply_chat_id, 
                f"Found **{len(matched_messages)}** raw files.\n"
                f"✅ Segregated into **{len(seasons_data)}** unique seasons. Passing to processor..."
            )

            await generate_season_cards(seasons_data, reply_chat_id)

            # await process_files(matched_messages, reply_chat_id)
        else:
            await bot.send_message(
                reply_chat_id, 
                f"❌ No files matching `{search_query}` were found in the channel history."
            )

    except Exception as e:
        logger.error(f"Error during optimized ingestion execution: {e}")
        await bot.send_message(reply_chat_id, f"❌ **Error during ingestion:** `{e}`")