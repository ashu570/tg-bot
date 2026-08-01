import time
import math
import logging
from src.helper.commons import CANCELLED_EVENTS
from telethon import Button

logger = logging.getLogger(__name__)

class ProcessCancelledError(Exception):
    pass

class ProgressTracker:
    #Todo: Convert this class so that we can have multiple types of progress tracker
    def __init__(self, status_message,file_index, batch_index,total_batches, total_files, chat_id, season_name, type:str = 'Download'): #Default argument follows non-default argument
        self.status_message = status_message
        self.file_index = file_index
        self.total_files = total_files
        self.start_time = time.time()
        self.last_update = 0
        self.type = type
        self.chat_id = chat_id
        self.season_name = season_name
        self.total_batches = total_batches
        self.batch_index = batch_index
    async def __call__(self, current, total):
        cancel_event = CANCELLED_EVENTS.get(self.chat_id)
        if cancel_event and cancel_event.is_set():
            logger.info(f"Cancel event detected for chat_id {self.chat_id}. Stopping {self.type}.")
            raise ProcessCancelledError("Process was cancelled by the user.")
        now = time.time()
        if now - self.last_update < 3 and current < total:
            return
        self.last_update = now
        
        percent = (current / total) * 100
        speed = current / (now - self.start_time)
        eta_seconds = (total - current) / speed if speed > 0 else 0.00001

        minutes = int(eta_seconds // 60)
        seconds = int(eta_seconds % 60)
        eta = f"{minutes}m {seconds}s" if minutes>0 else f"{seconds}s"
        
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        speed_mb = speed / (1024 * 1024)
        
        text = (
            f"🎬 **{self.season_name}** [Batch: {self.batch_index}/{self.total_batches}]\n"
            f"⏳ **{self.type}ing File {self.file_index} of {self.total_files}**\n"
            f"📊 **Progress:** {percent:.1f}% ({current_mb:.1f} MB / {total_mb:.1f} MB)\n"
            f"🚀 **Speed:** {speed_mb:.2f} MB/s\n"
            f"⏱ **ETA:** {eta}"
        )
        
        try:
            await self.status_message.edit(text, buttons=[Button.inline("🛑 STOP", data=f"cancel|{self.chat_id}")])
        except Exception as e:
            logger.error(f"ProgressTracker: Failed to edit status message for chat_id {self.chat_id}: {e}")