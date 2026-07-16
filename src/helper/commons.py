import re
import os
import aiohttp
from guessit import guessit
from typing import Optional, Any
from src.libs.logger import logger

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
    
    async def make_request(self, url: str, method: str = "GET", response_format: str = "json", **kwargs) -> Any:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status != 200:
                        logger.error(f"HTTP Error {response.status} for {url}")
                        return None
                    if response_format == "json":
                        return await response.json()
                    elif response_format == "bytes":
                        return await response.read()
                    else:
                        return await response.text()
                    
            if os.name == 'nt':
                import asyncio
                await asyncio.sleep(0.25) #We sleep for 0.25 second so Windows doesn't panic, look for Exception in callback _ProactorBasePipeTransport
            return data
        except Exception as e:
            logger.exception(f"Request failed for {url}: {e}")
            return None
    
common_helper = CommonHelper()
ACTIVE_BATCHES = {}