import asyncio
from telethon.errors import FloodWaitError # Assuming you are using Telethon
from src.libs.user_client import userbot
from config import config
from src.plugin.indexer import db

async def initial_sync(start_message_id=0):
    print("Booting up Userbot for historical sync...")
    await userbot.start()
    print(f"Connected. Starting sync on {config.tif_raw_channel}...")
    
    batch = []
    total_indexed = 0
    last_processed_id = start_message_id 

    while True:
        try:
            async for msg in userbot.iter_messages(config.tif_raw_channel, min_id=last_processed_id, reverse=True):
                if msg.media and (msg.document or msg.video):
                    file_name = msg.file.name if msg.file else ""
                    caption = msg.text or ""
                    batch.append((msg.id, file_name, caption))
                    if len(batch) >= 1000:
                        await asyncio.to_thread(db.save_new_files, batch)
                        total_indexed += len(batch)
                        last_processed_id = msg.id
                        print(f"Committed {total_indexed} files... Saved up to Message ID: {last_processed_id}")
                        batch = []
                        await asyncio.sleep(0.2) 
            break 
        except FloodWaitError as e:
            print(f"⚠️ Hit Telegram rate limit! Sleeping for {e.seconds} seconds before resuming...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            # Todo: handle reconnection logic
            break 
    if batch:
        await asyncio.to_thread(db.save_new_files, batch)
        total_indexed += len(batch)
        
    print(f"✅ Sync complete! A total of {total_indexed} files are now indexed.")

if __name__ == "__main__":
    asyncio.run(initial_sync(0))