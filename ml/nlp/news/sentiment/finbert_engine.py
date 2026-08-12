import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class FinBERTSentimentEngine:
    """
    Financial sentiment analysis engine using ProsusAI/finbert.
    """
    MODEL_NAME = "ProsusAI/finbert"
    VERSION = "v1"
    
    def __init__(self, fallback_mode: bool = False):
        self.fallback_mode = fallback_mode or not HAS_TRANSFORMERS
        self.pipeline = None
        
        if self.fallback_mode:
            logger.warning(
                "transformers package not found or fallback_mode enabled. "
                "FinBERTSentimentEngine will run in dummy fallback mode. "
                "Install with: pip install transformers torch"
            )
        else:
            try:
                # Load pipeline. (Will download model weights on first run)
                self.pipeline = pipeline("sentiment-analysis", model=self.MODEL_NAME)
            except Exception as e:
                logger.error(f"Failed to load FinBERT model: {e}")
                self.fallback_mode = True

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment for a given text.
        Returns label (POSITIVE, NEGATIVE, NEUTRAL) and score.
        """
        if not text or len(text.strip()) == 0:
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "confidence": 0.0,
                "model_version": f"{self.MODEL_NAME}_{self.VERSION}",
                "is_generated": True
            }

        if self.fallback_mode:
            # Provide a naive heuristic for demonstration if dependencies are missing
            lower_text = text.lower()
            pos_words = ["surge", "jump", "growth", "profit", "beat", "up"]
            neg_words = ["plunge", "drop", "loss", "miss", "down", "warning"]
            
            pos_count = sum(1 for w in pos_words if w in lower_text)
            neg_count = sum(1 for w in neg_words if w in lower_text)
            
            if pos_count > neg_count:
                label = "POSITIVE"
                score = 0.8
            elif neg_count > pos_count:
                label = "NEGATIVE"
                score = -0.8
            else:
                label = "NEUTRAL"
                score = 0.0
                
            return {
                "label": label,
                "score": score,
                "confidence": abs(score),
                "model_version": "fallback_heuristic_v1",
                "is_generated": True
            }

        # Truncate text to 512 tokens (approx) if necessary
        # pipeline automatically truncates if we pass truncation=True, but let's be safe
        truncated_text = text[:2000]
        
        try:
            result = self.pipeline(truncated_text)[0]
            # FinBERT returns labels: "positive", "negative", "neutral"
            raw_label = result['label'].upper()
            confidence = result['score']
            
            # Map score to [-1, 1] for our internal storage if desired, 
            # but FinBERT score is just a softmax probability.
            # We will store the label and confidence separately.
            if raw_label == "POSITIVE":
                score = confidence
            elif raw_label == "NEGATIVE":
                score = -confidence
            else:
                score = 0.0
                
            return {
                "label": raw_label,
                "score": score,
                "confidence": confidence,
                "model_version": f"{self.MODEL_NAME}_{self.VERSION}",
                "is_generated": True # Mark as model-generated, not human-verified
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "confidence": 0.0,
                "model_version": f"{self.MODEL_NAME}_{self.VERSION}",
                "is_generated": True
            }
