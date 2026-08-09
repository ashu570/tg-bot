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
    runtime = tmdb_result.get("runtime", 0)
    rating = tmdb_result.get("rating", 0.0)
    imdb_id = tmdb_result.get("imdb_id", "")
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
    imdb_link = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else ""
    poster_url = tmdb_result.get("poster_url", "")
    
    card_text = f"**{title}** ({year}) • {media_type_str}\n"
    card_text += f"_{runtime}min_ ⭐{rating} [IMDB]({imdb_link})\n\n"
    if actors:
        card_text += f"Actors: {actors}\n\n"
    if formatted_genres:
        card_text += f"Genres: {formatted_genres}\n"
    if overview:
        card_text += f"{overview}\n"
    
    if poster_url:
        card_text += f"[\u200b]({poster_url})"
        
    return card_text