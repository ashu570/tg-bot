import uuid
from telethon import Button
from src.libs.user_client import bot
from src.libs.logger import logger
from src.helper.commons import ACTIVE_BATCHES, ACTIVE_SEASON_CARDS 

async def generate_season_cards(seasons_data: dict, chat_id: int):
    if not seasons_data:
        return
    ACTIVE_BATCHES[chat_id] = {}
    ACTIVE_SEASON_CARDS[chat_id] = []
    for season, qualities in sorted(seasons_data.items()):
        card_text = f"🎬 **{season}**\nSelect the quality and language tier you want to process:"
        keyboard = []
        for quality_key, episodes in qualities.items():
            short_hash = uuid.uuid4().hex[:6]
            ACTIVE_BATCHES[chat_id][short_hash] = list(episodes.values())
            ep_count = len(episodes)
            button_text = f"{quality_key} ({ep_count} EPs)"
            cb_data = f"p|{short_hash}".encode('utf-8')
            keyboard.append([Button.inline(button_text, data=cb_data)])
        keyboard.append([
            # Todo: Need to handle this efficiently
            Button.inline("⏬ Process ALL Qualities & Audio", data=f"p|{season}|ALL".encode('utf-8'))
        ])
        sent_msg = await bot.send_message(chat_id, card_text, buttons=keyboard)
        ACTIVE_SEASON_CARDS[chat_id].append(sent_msg.id)
    # if len(seasons_data) > 1 or (len(seasons_data) == 1 and "Movie" not in seasons_data):
    #     final_text = "📦 **Series Processing**\nDo you want to process everything across all seasons?"
    #     final_keyboard = [
    #         [Button.inline("🚀 Process Entire Series", data=b"p_all_series")]
    #     ]
    #     await bot.send_message(chat_id, final_text, buttons=final_keyboard)
        
    logger.info("Successfully generated and sent UI selection cards.")