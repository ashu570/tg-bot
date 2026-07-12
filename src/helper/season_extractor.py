import re
from collections import defaultdict
from telethon.tl.custom import Message
from src.helper.commons import common_helper

def extract_metadata(text: str) -> tuple:
    season, episode, quality, language = "Unknown", "Unknown", "Unknown", "Unknown"
    s_match = re.search(r'[Ss](\d+)', text)
    e_match = re.search(r'[Ee](\d+)', text)
    q_match = re.search(r'(2160[pP]|1080[pP]|720[pP]|480[pP]|4[kK])', text)

    text_lower = text.lower()
    title = common_helper.clean_file_name(text_lower)
    if 'dual' in text_lower or 'multi' in text_lower:
        language = "Dual Audio"
    elif 'hindi' in text_lower:
        language = "Hindi"
    elif 'english' in text_lower:
        language = "English"
    else:
        language = 'Multi Lang'

    if s_match and e_match:
        season = f"S{int(s_match.group(1)):02d}"
        episode = f"E{int(e_match.group(1)):02d}"
    else: # For movie
        season = "Movie"
        episode = title if title else "Full Movie"

    quality = q_match.group(1).lower() if q_match else "NA"
    return season, episode, quality, language, title

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