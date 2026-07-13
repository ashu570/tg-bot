import re
import os
from src.helper.commons import common_helper

def format_video_metadata(original_name: str) -> tuple:
    base_name = os.path.basename(original_name)
    _, ext = os.path.splitext(base_name)
    ext = str(ext)

    metadata = common_helper.file_meta_extractor(original_name)
    #Todo: Get information from TMDB and actual picture
    title = metadata.get("title", "Unknown_Title")
    year = metadata.get("year")
    season = metadata.get("season")
    episode = metadata.get("episode")
    quality = metadata.get("quality")
    audio_tags = metadata.get("custom_audio", [])

    year_tag = str(year) if year else ""
    quality_tag = str(quality).lower() if quality else ""
    lang_tag = ".".join([a.title() for a in audio_tags])
    
    se_tag = ""
    if season is not None and episode is not None:
        se_tag = f"S{int(season):02d}E{int(episode):02d}"
    elif season is not None:
        se_tag = f"S{int(season):02d}"
    elif episode is not None:
        se_tag = f"E{int(episode):02d}"

    clean_title_dotted = title.replace(" ", ".")
    file_components = [clean_title_dotted, year_tag, se_tag, lang_tag, quality_tag]
    final_file_components = [c for c in file_components if c]
    final_name = ".".join(final_file_components) + ext
    
    caption_parts = [title]
    if year_tag:
        caption_parts.append(f"({year_tag})")
    if se_tag:
        caption_parts.append(se_tag)
    if quality_tag:
        caption_parts.append(quality_tag)
    if lang_tag:
        caption_parts.append(f"({lang_tag.replace('.', ' ')})")    
    final_caption = " ".join(caption_parts)
    
    return final_name, final_caption