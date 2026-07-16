import asyncio
from telethon import events
from src.libs.logger import logger
from src.libs.user_client import bot
from src.pipeline.ingestion import ingest_raw_files 
from src.helper.commons import ACTIVE_BATCHES
from src.pipeline.processing import handle_series_selection

@bot.on(events.NewMessage(pattern=r'^/process (.+)$', incoming=True))
async def trigger_processing(event):
    if not event.is_private:
        return
    search_query = event.pattern_match.group(1).strip()
    if not search_query:
        await event.respond("⚠️ Please provide a search term. Example: `/process named video`")
        return
    asyncio.create_task(ingest_raw_files(event.chat_id, search_query))

@bot.on(events.CallbackQuery(pattern=b'^p\|'))
async def handle_season_processing(event):
    data = event.data.decode('utf-8')
    _, target_hash = data.split('|')
    
    await event.answer("Initializing batch...", alert=False)
    await event.edit("⏳ **Initializing Processing...**")
    asyncio.create_task(handle_series_selection(event.chat_id, target_hash))