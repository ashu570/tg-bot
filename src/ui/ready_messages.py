from config import config
from src.libs.user_client import userbot
import os

ASSETS_DIR = 'assets'

SMALL_CAPS_MAP = {
    "A": "ᴀ",
    "B": "ʙ",
    "C": "ᴄ",
    "D": "ᴅ",
    "E": "ᴇ",
    "F": "ꜰ",
    "G": "ɢ",
    "H": "ʜ",
    "I": "ɪ",
    "J": "ᴊ",
    "K": "ᴋ",
    "L": "ʟ",
    "M": "ᴍ",
    "N": "ɴ",
    "O": "ᴏ",
    "P": "ᴘ",
    "Q": "ꞯ",
    "R": "ʀ",
    "S": "ꜱ",
    "T": "ᴛ",
    "U": "ᴜ",
    "V": "ᴠ",
    "W": "ᴡ",
    "X": "ˣ",
    "Y": "ʏ",
    "Z": "ᴢ",
}


def to_small_caps(text: str) -> str:
    return "".join(
        SMALL_CAPS_MAP.get(ch.upper(), ch)
        if ch.isascii() and ch.isalpha()
        else ch
        for ch in str(text)
    )


async def generate_series_banner():
    pass


def build_tmdb_card(tmdb_result: dict, fallback_series_name: str = "Unknown") -> str:
    title = to_small_caps(tmdb_result.get("title") or fallback_series_name)
    year = tmdb_result.get("year", "")
    media_type_str = to_small_caps("TVSeries" if tmdb_result.get("media_type") == "tv" else "Movie")
    rating = tmdb_result.get("rating", 0.0)
    actors = ", ".join(tmdb_result.get("actors", []))
    
    genre_emojis = {
        "Action": "Action", "Adventure": "🌋 Adventure", "Drama": "🎭 Drama", 
        "Fantasy": "✨ Fantasy", "Comedy": "😂 Comedy", "Horror": "👻 Horror", 
        "Science Fiction": "👽 Sci-Fi", "Sci-Fi & Fantasy": "👽 Sci-Fi & Fantasy",
        "Animation": "🎨 Animation", "Mystery": "🕵️ Mystery", "Thriller": "🔪 Thriller", 
        "Crime": "🚔 Crime", "Romance": "❤️ Romance", "Family": "👨‍👩‍👧‍👦 Family"
    }
    genres_list = tmdb_result.get("genres", [])
    formatted_genres = ", ".join([genre_emojis.get(g, g) for g in genres_list])
    
    overview = tmdb_result.get("overview", "")
    poster_url = tmdb_result.get("poster_url", "")
    
    card_text = f"**{to_small_caps(title)}** ({year}) • {media_type_str}\n"
    if actors:
        card_text += f"{to_small_caps('Actors')}: {actors}\n\n"
    if formatted_genres:
        card_text += f"{to_small_caps('Genres')}: {formatted_genres}\n"
    if overview:
        card_text += f"{overview}\n"
    
    if poster_url:
        card_text += f"[\u200b]({poster_url})"
        
    return card_text

def build_quality_cards(successful_links: dict, final_meta: dict) -> list[str]:
    title = final_meta.get("title", "UNKNOWN TITLE").upper()
    year = final_meta.get("year", "")
    year_str = f" • {year}" if year else ""
    
    cards = []
    
    for quality, seasons in successful_links.items():
        formatted_quality = quality.upper().strip()
        caption = f"🎭 **{to_small_caps(title)}{year_str}**\n"
        caption += f"📦 **{to_small_caps('QUALITY')} - {to_small_caps(formatted_quality)}**\n\n"
        
        def get_season_num(s_key):
            try:
                return int(s_key.split('#')[-1])
            except:
                return 999
                
        for season_key, audios in sorted(seasons.items(), key=lambda x: get_season_num(x[0])):
            season_display = season_key.replace('#', ' ').upper()
            caption += f"🔹 **{season_display}**\n"
            audio_links = []
            for audio_tag, link in audios.items():
                audio_display = audio_tag.upper().strip()
                audio_links.append(f"[{to_small_caps(audio_display)}]({link})")
            caption += f" || {' || '.join(audio_links)} ||\n\n"
            
        caption += "***Click on the required audio and then Press Start in the bot***"
        cards.append(caption)
        
    return cards

async def send_final_ready_sticker():
    sticker_path = os.path.join(ASSETS_DIR, "shadow_sticker.webp")
    if os.path.exists(sticker_path):
        await userbot.send_message(config.ready_channel, file=sticker_path)