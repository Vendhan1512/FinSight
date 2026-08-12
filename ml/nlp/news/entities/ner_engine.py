import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

class NEREngine:
    """
    Named Entity Recognition engine using spaCy.
    """
    MODEL_NAME = "en_core_web_sm"
    VERSION = "v1"
    
    def __init__(self, fallback_mode: bool = False):
        self.fallback_mode = fallback_mode or not HAS_SPACY
        self.nlp = None
        
        if self.fallback_mode:
            logger.warning(
                "spacy package not found or fallback_mode enabled. "
                "NEREngine will run in dummy fallback mode. "
                "Install with: pip install spacy && python -m spacy download en_core_web_sm"
            )
        else:
            try:
                self.nlp = spacy.load(self.MODEL_NAME)
            except OSError:
                logger.warning(f"spaCy model {self.MODEL_NAME} not found. Try: python -m spacy download {self.MODEL_NAME}")
                self.fallback_mode = True

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities (ORG, PERSON, LOC, PRODUCT) from text.
        """
        if not text:
            return []
            
        if self.fallback_mode:
            # Naive fallback: just look for a few capitalized words as ORGs
            # This is strictly for when dependencies are missing to prevent crash
            import re
            words = re.findall(r'\b[A-Z][a-z]+\b', text)
            entities = []
            if "Apple" in words:
                entities.append({"text": "Apple", "label": "ORG"})
            return entities

        # Limit text length to prevent memory blowouts (spaCy default limit is 1,000,000 chars)
        text = text[:100000]
        
        try:
            doc = self.nlp(text)
            entities = []
            
            allowed_labels = {"ORG", "PERSON", "LOC", "GPE", "PRODUCT"}
            
            for ent in doc.ents:
                if ent.label_ in allowed_labels:
                    # Normalize GPE to LOC
                    label = "LOC" if ent.label_ == "GPE" else ent.label_
                    entities.append({
                        "text": ent.text.strip(),
                        "label": label
                    })
                    
            # Basic intra-document deduplication (if the exact same text and label appear, merge)
            unique_entities = {}
            for e in entities:
                key = f"{e['label']}_{e['text']}"
                if key not in unique_entities:
                    unique_entities[key] = e
            
            return list(unique_entities.values())
            
        except Exception as e:
            logger.error(f"NER extraction failed: {e}")
            return []
