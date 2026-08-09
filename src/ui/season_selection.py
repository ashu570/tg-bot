import re
import uuid
from telethon import Button
from src.libs.user_client import bot
from src.libs.logger import logger
from src.helper.commons import ACTIVE_BATCHES, ACTIVE_SEASON_CARDS 

async def generate_season_cards(seasons_data: dict, chat_id: int, current_index: int = 1, total_queries: int = 1, search_query: str = ""):
    if not seasons_data:
        return
    if chat_id not in ACTIVE_BATCHES:
        ACTIVE_BATCHES[chat_id] = {}
    if chat_id not in ACTIVE_SEASON_CARDS:
        ACTIVE_SEASON_CARDS[chat_id] = []

    grouped_series = {}
    for season, qualities in sorted(seasons_data.items()):
        match = re.match(r"(.+?)\s+S\d{2}$", season, re.IGNORECASE)
        series_title = match.group(1).strip() if match else season
        grouped_series.setdefault(series_title, []).append((season, qualities))

    for series_title, season_items in sorted(grouped_series.items()):
        group_quality_hashes = []
        for season, qualities in season_items:
            card_text = (
                f"📦 **[Batch: {current_index}/{total_queries}] Query:** `{search_query}`\n"
                f"🎬 **{season}**\n"
                f"Select the quality and language tier you want to process:"
            )
            keyboard = []
            season_quality_hashes = []
            for quality_key, episodes in qualities.items():
                short_hash = uuid.uuid4().hex[:6]
                season_quality_hashes.append(short_hash)
                group_quality_hashes.append(short_hash)
                ACTIVE_BATCHES[chat_id][short_hash] = list(episodes.values())
                ep_count = len(episodes)
                button_text = f"{quality_key} ({ep_count} EPs)"
                cb_data = f"p|{short_hash}".encode('utf-8')
                keyboard.append([Button.inline(button_text, data=cb_data)])

            if season_quality_hashes:
                season_hash = uuid.uuid4().hex[:6]
                ACTIVE_BATCHES[chat_id][season_hash] = "#".join(season_quality_hashes)
                keyboard.append([Button.inline("⏬ Process ALL Qualities & Audio", data=f"p|{season_hash}".encode('utf-8'))])

            sent_msg = await bot.send_message(chat_id, card_text, buttons=keyboard)
            ACTIVE_SEASON_CARDS[chat_id].append(sent_msg.id)

        if len(season_items) > 1 and group_quality_hashes:
            series_hash = uuid.uuid4().hex[:6]
            ACTIVE_BATCHES[chat_id][series_hash] = "#".join(group_quality_hashes)
            series_card_text = (
                f"📦 **[Batch: {current_index}/{total_queries}] Query:** `{search_query}`\n"
                f"🎬 **{series_title}**\n"
                f"Process all seasons in this series together:"
            )
            sent_msg = await bot.send_message(chat_id, series_card_text, buttons=[[Button.inline("⏬ Process ALL Seasons", data=f"p|{series_hash}".encode('utf-8'))]])
            ACTIVE_SEASON_CARDS[chat_id].append(sent_msg.id)

    logger.info("Successfully generated and sent UI selection cards.")