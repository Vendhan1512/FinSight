import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EntityResolver:
    """
    Resolves raw extracted entities to canonical entities.
    Does not guess ambiguous entities without evidence.
    """
    
    def __init__(self):
        # A simple mock knowledge base for resolution (in a real system, this queries a DB of companies)
        self.knowledge_base = {
            "apple": {"canonical_name": "Apple Inc.", "ticker": "AAPL"},
            "apple inc": {"canonical_name": "Apple Inc.", "ticker": "AAPL"},
            "apple inc.": {"canonical_name": "Apple Inc.", "ticker": "AAPL"},
            "microsoft": {"canonical_name": "Microsoft Corporation", "ticker": "MSFT"},
            "tesla": {"canonical_name": "Tesla, Inc.", "ticker": "TSLA"},
            "amazon": {"canonical_name": "Amazon.com, Inc.", "ticker": "AMZN"},
            "google": {"canonical_name": "Alphabet Inc.", "ticker": "GOOGL"},
            "alphabet": {"canonical_name": "Alphabet Inc.", "ticker": "GOOGL"},
            "meta": {"canonical_name": "Meta Platforms, Inc.", "ticker": "META"},
            "facebook": {"canonical_name": "Meta Platforms, Inc.", "ticker": "META"},
        }
        
        # Ambiguous names that shouldn't be resolved without context
        self.ambiguous = {"target", "square", "block", "zoom"}

    def resolve(self, raw_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes raw entities like [{"text": "Apple", "label": "ORG"}]
        Returns resolved entities suitable for NewsArticleEntity model.
        """
        resolved_results = []
        
        # Group aliases by canonical entity
        grouped = {}
        unresolved = []
        
        for ent in raw_entities:
            text = ent["text"]
            label = ent["label"]
            
            lower_text = text.lower()
            
            if lower_text in self.ambiguous:
                # Mark unresolved due to ambiguity
                unresolved.append({
                    "entity_type": label,
                    "canonical_name": text,
                    "aliases": [text],
                    "ticker": None,
                    "canonical_entity_id": None,
                    "resolution_method": "unresolved_ambiguous",
                    "resolution_confidence": 0.0
                })
                continue
                
            if label == "ORG" and lower_text in self.knowledge_base:
                kb_entry = self.knowledge_base[lower_text]
                canonical_name = kb_entry["canonical_name"]
                
                if canonical_name not in grouped:
                    grouped[canonical_name] = {
                        "entity_type": "ORG",
                        "canonical_name": canonical_name,
                        "aliases": set(),
                        "ticker": kb_entry.get("ticker"),
                        "canonical_entity_id": kb_entry.get("ticker"), # For now, ticker is canonical ID
                        "resolution_method": "exact_match_kb",
                        "resolution_confidence": 1.0
                    }
                grouped[canonical_name]["aliases"].add(text)
            else:
                # Unresolved entity
                unresolved.append({
                    "entity_type": label,
                    "canonical_name": text,
                    "aliases": [text],
                    "ticker": None,
                    "canonical_entity_id": None,
                    "resolution_method": "unresolved_unknown",
                    "resolution_confidence": 0.0
                })
                
        # Convert grouped sets to lists
        for data in grouped.values():
            data["aliases"] = list(data["aliases"])
            resolved_results.append(data)
            
        resolved_results.extend(unresolved)
        return resolved_results
