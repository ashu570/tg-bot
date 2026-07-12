import asyncio
from telethon import events
from src.libs.logger import logger
from src.libs.user_client import bot
from src.pipeline.ingestion import ingest_raw_files 

@bot.on(events.NewMessage(pattern=r'^/process (.+)$', incoming=True))
async def trigger_processing(event):
    if not event.is_private:
        return
    search_query = event.pattern_match.group(1).strip()
    if not search_query:
        await event.respond("⚠️ Please provide a search term. Example: `/process named video`")
        return
        
    await event.respond(f"🔍 Initializing optimized search for: `{search_query}`...")
    asyncio.create_task(ingest_raw_files(event.chat_id, search_query))