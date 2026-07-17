import sqlite3
import os
from src.libs.logger import logger

# Automatically detect the operating system to prevent path crashes
if os.name == 'nt':  
    DEFAULT_DB_PATH = "raw_channel_index.db"
else:
    DEFAULT_DB_PATH = "/home/ubuntu/raw_channel_index.db"

class SQLiteIndexer:
    def __init__(self, db_path=DEFAULT_DB_PATH): 
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._setup()

    def _setup(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                message_id INTEGER PRIMARY KEY,
                file_name TEXT,
                caption TEXT,
                created_on DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def get_last_synced_id(self) -> int:
        self.cursor.execute("SELECT MAX(message_id) FROM files")
        result = self.cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def fetch_all_records(self) -> list:
        try:
            logger.info("Inside SQLiteIndexer -> fetch_all_records")
            self.cursor.execute("SELECT message_id, file_name, caption FROM files")
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"CAUGHT: Error in SQLiteIndexer -> fetch_all_records {e}")
            return []

    def save_new_files(self, file_batch: list):
        if not file_batch:
            logger.debug("save_new_files called with an empty batch. Skipping write.")
            return
        try:
            self.cursor.executemany(
                "INSERT OR IGNORE INTO files (message_id, file_name, caption) VALUES (?, ?, ?)",
                file_batch
            )
            self.conn.commit()
            logger.info(f"Successfully indexed {len(file_batch)} new files into the database.")            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Unexpected error while saving files: {e}")

db = SQLiteIndexer()