import re
import os
import aiohttp
import shutil
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

        audio_pattern = r'(?i)(?<![a-z])(hindi|hin|english|eng|dual|multi)(?:[\s/*._$&#\-]*audio)?(?![a-z])'
        sub_pattern = r'(?i)(?<![a-z])(e|m|multi|dual|h|kor|spanish|hin|eng|hindi|english|engish|korean|german|ger|it|italian|ru|russian)?[\s/*._$&#\-]*(?:subs?|subtitles?)(?![a-z])'
        extracted_audio_raw = [lang.lower() for lang in re.findall(audio_pattern, re.sub(sub_pattern, '', name))]
        audio_tags = [language_map.get(lang, lang) for lang in extracted_audio_raw]
        sub_tags = [lang.lower() for lang in re.findall(sub_pattern, name) if lang]
        
        guessed_data = guessit(clean_name)
        title = guessed_data.get('title', clean_name)
        final_title = re.sub(r'\s+', ' ', str(title)).strip().title()
        metadata = {
            "title": final_title,
            "season": guessed_data.get('season'),
            "episode": guessed_data.get('episode'),
            "year": guessed_data.get('year'),
            "quality": guessed_data.get('screen_size'),
            "custom_audio": audio_tags,
            "custom_subs": sub_tags
        }
        return metadata
    
    #Use this method to call APIs 
    async def make_request(self, url: str, method: str = "GET", response_format: str = "json", **kwargs) -> Any:
        try:
            timeout = aiohttp.ClientTimeout(total=10.0) #Remove it if we ever need to get rid of the max timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
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
        
    def clean_directory(self, dir_path: str):
        logger.info(f"Cleaning {dir_path}")
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path, exist_ok=True)
    
common_helper = CommonHelper()
ACTIVE_BATCHES = {}
CANCELLED_EVENTS = {}
ACTIVE_SEASON_CARDS={}
language_map = {
    'e': 'English',
    'eng': 'English',
    'english': 'English',
    'h': 'Hindi',
    'hin': 'Hindi',
    'hindi': 'Hindi',
    'm': 'Multi',
    'multi': 'Multi',
    'dual': 'Dual',
    'kor': 'Korean',
    'korean': 'Korean',
    'ger': 'German',
    'german': 'German',
    'it': 'Italian',
    'italian': 'Italian',
    'ru': 'Russian',
    'russian': 'Russian',
    'spanish': 'Spanish',
    'dual': "Dual",
    'multi': "Multi"
}