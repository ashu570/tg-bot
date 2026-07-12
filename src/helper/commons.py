import re

class CommonHelper:
    def clean_file_name(self, text:str):
        tv_tags = r'(?i)([Ss]\d+[\.\-\s]*[Ee]\d+|\b[Ss]\d+\b|\b\d+x\d+\b).*'
        clean_name = re.sub(r'\.\w{2,4}$', '', text)
        tags = r'(?i)(2160p|1080p|720p|480p|4k|dual|multi|hindi|english|audio|x264|x265|hevc|bluray|web-dl|amzn|nf)'
        clean_name = re.sub(tags, '', clean_name)
        # Strip S01E01 and everything after it for TV shows
        clean_name = re.sub(tv_tags, '', clean_name)
        clean_name = re.sub(r'(19\d{2}|20\d{2})', '', clean_name)
        clean_name = re.sub(r'[\.\-\_\[\]\(\)]', ' ', clean_name)
        title = re.sub(r'\s+', ' ', clean_name).strip().title()
        
        return title


common_helper = CommonHelper()
ACTIVE_BATCHES = {}