import asyncio
from src.libs.user_client import userbot
from config import config
from src.plugin.indexer import db

async def initial_sync():
    print("Booting up Userbot for historical sync...")
    await userbot.start()
    print(f"Connected. Starting massive historical sync on {config.raw_channel}...")
    print("This may take a few minutes depending on channel size. Please wait.")
    
    batch = []
    total_indexed = 0
    async for msg in userbot.iter_messages(config.raw_channel):
        if msg.media and (msg.document or msg.video):
            file_name = ""
            if msg.document:
                for attr in msg.document.attributes:
                    if hasattr(attr, 'file_name'):
                        file_name = attr.file_name
                        break
                        
            caption = msg.text or ""
            batch.append((msg.id, file_name, caption))
            if len(batch) >= 1000:
                db.save_new_files(batch)
                total_indexed += len(batch)
                print(f"Successfully committed {total_indexed} files to the database...")
                batch = []
                await asyncio.sleep(1)  #Flood prevention
    if batch:
        db.save_new_files(batch)
        total_indexed += len(batch)
        
    print(f"✅ Sync complete! A total of {total_indexed} files are now indexed and ready for production.")

if __name__ == "__main__":
    asyncio.run(initial_sync())