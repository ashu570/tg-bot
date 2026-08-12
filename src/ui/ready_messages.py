from config import config
from src.libs.user_client import userbot
import os

ASSETS_DIR = 'assets'

async def generate_series_banner():
    pass

def build_tmdb_card(tmdb_result: dict, fallback_series_name: str = "Unknown") -> str:
    title = (tmdb_result.get("title") or fallback_series_name).upper()
    year = tmdb_result.get("year", "")
    media_type_str = "TVSeries" if tmdb_result.get("media_type") == "tv" else "Movie"
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
    
    card_text = f"**{title}** ({year}) • {media_type_str}\n"
    if actors:
        card_text += f"Actors: {actors}\n\n"
    if formatted_genres:
        card_text += f"Genres: {formatted_genres}\n"
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
        caption = f"🎭 **{title}{year_str}**\n"
        caption += f"📦 **QUALITY - {formatted_quality}**\n\n"
        
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
                audio_links.append(f"[{audio_display}]({link})")
            caption += f" || {' || '.join(audio_links)} ||\n\n"
            
        caption += "_Click on the required audio and then Press Start in the bot_"
        cards.append(caption)
        
    return cards