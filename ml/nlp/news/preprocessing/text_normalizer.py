import re
import html
import unicodedata

class TextNormalizer:
    """
    Cleans and normalizes news text non-destructively for NLP processing.
    """
    
    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""
            
        # 1. Unescape HTML entities
        text = html.unescape(text)
        
        # 2. Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 3. Normalize Unicode (NFKC handles ligatures and full-width chars)
        text = unicodedata.normalize('NFKC', text)
        
        # 4. Remove Zero-width characters and control characters (except newline)
        text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff]', '', text)
        
        # 5. Collapse excessive whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 6. Handle truncation markers often left by APIs (e.g. [+1234 chars])
        text = re.sub(r'\[\+\d+\s*chars\]', '', text, flags=re.IGNORECASE)
        
        return text.strip()
