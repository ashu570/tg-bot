import asyncio
from telethon import events
from telethon.errors import FloodWaitError
from src.libs.logger import logger
from src.libs.user_client import bot
from src.pipeline.ingestion import ingest_raw_files 
from src.helper.commons import ACTIVE_BATCHES, CANCELLED_EVENTS, ACTIVE_SEASON_CARDS, USER_SESSIONS, common_helper
from src.pipeline.processing import handle_series_selection
from config import config

@bot.on(events.NewMessage(pattern=r'^/process (.+)$', incoming=True))
async def trigger_processing(event):
    if not event.is_private:
        return
    chat_id = event.chat_id
    session = USER_SESSIONS.get(chat_id)
    if session and session.get('queued_payloads') is not None and  session.get('queued_payloads'):
        await event.respond("⚠️ A process is already running! Please wait for it to finish before starting a new one.")
        return
    raw_queries = event.pattern_match.group(1).strip()
    queries = [q.strip() for q in raw_queries.split(',') if q.strip()]
    ACTIVE_BATCHES.pop(chat_id, None)
    await event.respond(f"🔍 Starting batch process for **{len(queries)}** queries...")
    USER_SESSIONS[chat_id] = {
            'pending_queries': queries,
            'queued_payloads': [],
            'total_queries': len(queries),
            'current_index': 1
    }
    task = asyncio.create_task(advance_session(chat_id))
    USER_SESSIONS[chat_id]['task'] = task

async def advance_session(chat_id):
    session = USER_SESSIONS.get(chat_id)
    if not session:
        return
    try:
        if session['pending_queries']:
            next_query = session['pending_queries'].pop(0)
            logger.info(f"Session {chat_id}: Advancing to next query -> {next_query}")
            await ingest_raw_files(chat_id, next_query, session['current_index'], session['total_queries'])
        else:
            payloads = session['queued_payloads']
            if not payloads:
                await bot.send_message(chat_id, "⚠️ Queue is empty. No selections were made.")
                USER_SESSIONS.pop(chat_id, None)
                return
            task = asyncio.create_task(execute_queue(chat_id, payloads))
            session['task'] = task
    except Exception as e:
        logger.error(f"❌ Error in advance_session for {chat_id}: {e}")
        USER_SESSIONS.pop(chat_id, None)

async def execute_queue(chat_id, payloads):
    try:
        for target_hash in payloads:
            await handle_series_selection(chat_id, target_hash)
        await bot.send_message(chat_id, "🎉 Batch processing fully complete!")
    finally:
        USER_SESSIONS.pop(chat_id, None)
    

@bot.on(events.CallbackQuery(pattern=rb'^p\|'))
async def handle_season_processing(event):
    data = event.data.decode('utf-8')
    _, target_hash = data.split('|')
    chat_id = event.chat_id
    message_ids = ACTIVE_SEASON_CARDS.get(chat_id, [])
    if message_ids:
        try:
            await bot.delete_messages(chat_id, message_ids)
        except Exception as e:
            logger.error(f"Failed to delete season cards: {e}")
        finally:
            ACTIVE_SEASON_CARDS.pop(chat_id, None)

    session = USER_SESSIONS.get(chat_id)
    if session:
        session['queued_payloads'].append(target_hash)
        session['current_index'] += 1
        asyncio.create_task(advance_session(chat_id))
    else:
        asyncio.create_task(handle_series_selection(chat_id, target_hash))

@bot.on(events.CallbackQuery(pattern=rb'cancel\|(\d+)'))
async def handle_cancel_processing(event):
    chat_id = int(event.pattern_match.group(1))
    if chat_id in CANCELLED_EVENTS:
        CANCELLED_EVENTS[chat_id].set()
        await event.answer("Stopping process safely... Please wait.", alert=True)
    else:
        await event.answer("No active process to cancel.", alert=True)

@bot.on(events.NewMessage(pattern=r'^/start(?: |$)(.*)', incoming=True))
async def handle_start_command(event):
    if not event.is_private:
        return
    payload = event.pattern_match.group(1).strip()
    if not payload:
        await event.respond("👋 Hello! I am the orchestrator bot. Send me a command to begin.")
        return
    try:
        decoded_string = common_helper.decode_payload(payload)
        args = decoded_string.split("-")
        if args[0] != "get":
            return
        channel_id_abs = abs(config.shadow_channel)
        if len(args) == 3:
            start_msg = int(int(args[1]) / channel_id_abs)
            end_msg = int(int(args[2]) / channel_id_abs)
            message_ids = list(range(start_msg, end_msg + 1))
        elif len(args) == 2:
            message_ids = [int(int(args[1]) / channel_id_abs)]
        else:
            return
    except Exception as e:
        logger.error(f"Invalid deep link payload '{payload}': {e}")
        await event.respond("⚠️ **Invalid or expired link.**")
        return
    temp_msg = await event.respond("⏳ **Fetching your files, please wait...**")
    try:
        messages = await bot.get_messages(config.shadow_channel, ids=message_ids)
        messages = [msg for msg in messages if msg is not None]
        if not messages:
            await temp_msg.edit("❌ **Files not found.** They might have been removed from the server.")
            return
        await temp_msg.delete()
        for msg in messages:
            try:
                await bot.send_message(event.chat_id, message=msg)
                await asyncio.sleep(0.5)
            except FloodWaitError as e:
                logger.warning(f"FloodWait while fetching files, sleeping for {e.seconds}s")
                await asyncio.sleep(e.seconds)
                await bot.send_message(event.chat_id, message=msg)
    except Exception as e:
        logger.exception(f"Error fetching shadow channel files: {e}")
        await event.respond("❌ **Something went wrong while fetching the files.**")

@bot.on(events.NewMessage(pattern=r'^/reset$', incoming=True))
async def reset_user_session(event):
    if not event.is_private:
        return
    chat_id = event.chat_id
    if chat_id in USER_SESSIONS:
        session = USER_SESSIONS[chat_id]
        if 'task' in session and not session['task'].done():
            session['task'].cancel()
        USER_SESSIONS.pop(chat_id, None)
        await event.respond("✅ **Session forcefully reset.** You can now start a new `/process`.")
    else:
        await event.respond("ℹ️ You don't have any active processes running.")