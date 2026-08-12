from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.models.monitoring import ModelPerformance
from app.models.ml import Prediction
from app.models.warehouse import MarketPrice

logger = logging.getLogger(__name__)

class PerformanceEngine:
    def __init__(self, db: Session):
        self.db = db
        
    def resolve_pending_predictions(self, model_version: str):
        """
        Find predictions whose horizon has elapsed and resolve them against actual MarketPrices.
        """
        # Find predictions that have not been scored yet (no ModelPerformance record)
        # We join to see if a ModelPerformance record exists.
        
        # For simplicity, we just fetch all predictions for the model
        # In production, we would use a left outer join to find missing records.
        pending_preds = self.db.query(Prediction).filter(
            Prediction.model_version == model_version
        ).all()
        
        resolved_count = 0
        
        for pred in pending_preds:
            # Check if it's already resolved
            existing = self.db.query(ModelPerformance).filter(
                ModelPerformance.prediction_id == pred.prediction_id
            ).first()
            
            if existing:
                continue
                
            horizon_days = 20 # Assuming 20-day horizon for our sprint ML model
            
            # Check if horizon has elapsed
            target_date = pred.prediction_time + timedelta(days=horizon_days)
            
            if datetime.utcnow() >= target_date:
                # Horizon has elapsed, find actuals
                # Look for the price at prediction_time
                price_t0 = self.db.query(MarketPrice).filter(
                    MarketPrice.entity_id == pred.entity_id,
                    MarketPrice.timestamp <= pred.prediction_time
                ).order_by(MarketPrice.timestamp.desc()).first()
                
                # Look for the price at target_date
                price_t1 = self.db.query(MarketPrice).filter(
                    MarketPrice.entity_id == pred.entity_id,
                    MarketPrice.timestamp >= target_date
                ).order_by(MarketPrice.timestamp.asc()).first()
                
                if price_t0 and price_t1:
                    # Calculate actual return
                    actual_return = (price_t1.close_price - price_t0.close_price) / price_t0.close_price
                    actual_class = "OUTPERFORM" if actual_return > 0 else "UNDERPERFORM"
                    
                    is_correct = 1 if actual_class == pred.predicted_value else 0
                    
                    perf = ModelPerformance(
                        prediction_id=pred.prediction_id,
                        prediction_time=pred.prediction_time,
                        prediction=pred.predicted_value,
                        prediction_probability=pred.prediction_probability,
                        actual=actual_class,
                        horizon=horizon_days,
                        model_version=model_version,
                        is_correct=is_correct,
                        calculated_at=datetime.utcnow()
                    )
                    self.db.add(perf)
                    resolved_count += 1
                    
        if resolved_count > 0:
            self.db.commit()
            logger.info(f"Resolved {resolved_count} pending predictions for {model_version}")
            
        return resolved_count
