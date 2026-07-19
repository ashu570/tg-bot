import re
from collections import defaultdict
from telethon.tl.custom import Message
from src.helper.commons import common_helper

#Todo: Optimize
def extract_metadata(text: str) -> tuple:
    season, episode = "Unknown", "Unknown"
    q_match = re.search(r'(2160[pP]|1080[pP]|720[pP]|480[pP]|4[kK])', text)
    text_lower = text.lower()
    file_meta = common_helper.file_meta_extractor(text_lower)
    if file_meta.get('season') and file_meta.get('episode'):
        season = f"S{file_meta.get('season'):02d}"
        episode = f"E{file_meta.get('episode'):02d}"
    else: # For movie
        season = "Movie"
        episode = file_meta.get('title', 'Full Movie')

    quality = q_match.group(1).lower() if q_match else "NA"
    return season, episode, quality, ". ".join(file_meta.get("custom_audio",[])), file_meta.get('title', 'Default')

def segregate_and_dedupe(messages: list[Message]) -> dict:
    """
    Organizes messages into a nested dictionary:
    """
    seasons_data = defaultdict(lambda: defaultdict(dict))
    for msg in messages:
        file_name = ""
        if msg.document:
            for attr in msg.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name
                    break
        text_to_parse = file_name if file_name else (msg.text or "")
        season, episode, quality, language, title = extract_metadata(text_to_parse)
        if season == "Unknown" or episode == "Unknown":
            continue 
        quality_lang_key = f"{quality} {language}".strip()
        if episode in seasons_data[f"{title} {season}".strip().title()][quality_lang_key]:
           pass
        else:
            seasons_data[f"{title} {season}".strip().title()][quality_lang_key][episode] = msg

    return seasons_data