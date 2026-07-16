import re
import os
from guessit import guessit

class CommonHelper:
    def clean_file_name(self, text:str):
        file_metadata = self.file_meta_extractor(text)
        return file_metadata.get("title")
    
    def file_meta_extractor(self, original_name:str):
        name, _ = os.path.splitext(original_name)
        delim = r'[\.\-\_\$\&\%\#\*\s]'
        clean_name = re.sub(rf'^\d+{delim}+', '', name)

        #Todo: More better subtitle and audio pattern
        audio_pattern = r'(?i)\b(hindi|english|eng|dual|multi|dual[\-\s_]*audio|multi[\-\s_]*audio)\b'
        sub_pattern = r'(?i)\b(esub|hc[\-\s_]*esub|subs?|eng[\-\s_]*subs?)\b'
        extracted_audio = re.findall(audio_pattern, clean_name)
        extracted_subs = re.findall(sub_pattern, clean_name)

        # Clean up the extracted tags (lowercase, remove hyphens/underscores for consistency)
        # Using a set to remove duplicates if a tag appears twice
        audio_tags = list(set([a.lower().replace('-', ' ').replace('_', ' ') for a in extracted_audio]))
        sub_tags = list(set([s.lower().replace('-', ' ').replace('_', ' ') for s in extracted_subs]))

        guessed_data = guessit(clean_name)
        title = guessed_data.get('title', clean_name)
        final_title = re.sub(r'\s+', ' ', str(title)).strip().title()
        metadata = {
            "title": final_title,
            "season": guessed_data.get('season'),
            "episode": guessed_data.get('episode'),
            "year": guessed_data.get('year'),
            "quality": guessed_data.get('screen_size'),
            "custom_audio": ", ".join(audio_tags),
            "custom_subs": ", ".join(sub_tags)
        }
        return metadata
    
common_helper = CommonHelper()
ACTIVE_BATCHES = {}