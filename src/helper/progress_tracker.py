import time
import math
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    #Todo: Convert this class so that we can have multiple types of progress tracker
    def __init__(self, status_message, file_index, total_files, type:str = 'Download'):
        self.status_message = status_message
        self.file_index = file_index
        self.total_files = total_files
        self.start_time = time.time()
        self.last_update = 0
        self.type = type

    async def __call__(self, current, total):
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
            f"⏳ **{self.type}ing File {self.file_index} of {self.total_files}**\n"
            f"📊 **Progress:** {percent:.1f}% ({current_mb:.1f} MB / {total_mb:.1f} MB)\n"
            f"🚀 **Speed:** {speed_mb:.2f} MB/s\n"
            f"⏱ **ETA:** {math.ceil(eta)} seconds"
        )
        
        try:
            await self.status_message.edit(text)
        except Exception:
            pass