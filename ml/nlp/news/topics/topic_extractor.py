import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

class TopicExtractor:
    """
    Reproducible rule/keyword-based topic extraction for financial news.
    Prevents LLM hallucinations by mapping strictly to predefined clusters.
    """
    
    MODEL_VERSION = "keyword_taxonomy_v1"
    
    def __init__(self):
        # A simple taxonomy of financial topics and associated keywords
        self.taxonomy = {
            "Earnings": [r'\bearnings\b', r'\beps\b', r'\brevenue\b', r'\bguidance\b', r'\bprofit\b', r'\bquarterly results\b'],
            "M&A": [r'\bmerger\b', r'\bacquisition\b', r'\bbuyout\b', r'\btakeover\b', r'\bspinoff\b'],
            "Macroeconomics": [r'\binflation\b', r'\binterest rate\b', r'\bfed\b', r'\bfederal reserve\b', r'\bcpi\b', r'\bgdp\b', r'\bjobless claims\b'],
            "Regulatory": [r'\bsec\b', r'\blawsuit\b', r'\bregulation\b', r'\bfine\b', r'\bantitrust\b', r'\binvestigation\b'],
            "Product Launch": [r'\bnew product\b', r'\bannounces\b', r'\brollout\b', r'\bfeatures\b', r'\bupgrade\b'],
            "Market Movement": [r'\bshares up\b', r'\bshares down\b', r'\bstock surges\b', r'\bstock plunges\b', r'\bselloff\b', r'\brally\b']
        }
        
        # Precompile regexes for performance
        self.compiled_taxonomy = {
            topic: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for topic, patterns in self.taxonomy.items()
        }

    def extract_topics(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract topics from text based on keyword matches.
        Returns a list of topics with scores representing hit counts or normalized scores.
        """
        if not text:
            return []
            
        topics_found = []
        
        for topic, patterns in self.compiled_taxonomy.items():
            hits = 0
            for pattern in patterns:
                # Find all non-overlapping matches
                matches = pattern.findall(text)
                hits += len(matches)
                
            if hits > 0:
                # Naive score: cap at 1.0 based on 3 hits
                score = min(hits / 3.0, 1.0)
                topics_found.append({
                    "topic_name": topic,
                    "topic_score": round(score, 2),
                    "model_version": self.MODEL_VERSION,
                    "is_generated": False
                })
                
        # Sort by score descending
        topics_found.sort(key=lambda x: x["topic_score"], reverse=True)
        return topics_found
