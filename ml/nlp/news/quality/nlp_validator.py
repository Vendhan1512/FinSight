import logging
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)

class NLPValidator:
    """
    Validates NLP outputs for quality and integrity.
    Does not silently discard, but logs failures and returns quality flags.
    """
    
    @staticmethod
    def validate_article(article_text: str) -> Dict[str, Any]:
        """
        Check if the article text is suitable for NLP processing.
        """
        if not article_text or len(article_text.strip()) == 0:
            return {"valid": False, "reason": "empty_text"}
            
        if len(article_text.strip()) < 50:
            return {"valid": False, "reason": "extremely_short_content"}
            
        # Assuming language is checked before or by another layer (e.g. fasttext),
        # but here we just pass it if it meets length requirements.
        return {"valid": True, "reason": "ok"}
        
    @staticmethod
    def validate_entities(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check quality of extracted and resolved entities.
        """
        unresolved_count = 0
        ambiguous_count = 0
        
        for ent in entities:
            if ent.get("resolution_method") == "unresolved_ambiguous":
                ambiguous_count += 1
            elif ent.get("canonical_entity_id") is None:
                unresolved_count += 1
                
        return {
            "total_extracted": len(entities),
            "unresolved_count": unresolved_count,
            "ambiguous_count": ambiguous_count
        }
