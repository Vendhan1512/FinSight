import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.monitoring import FeatureDriftMetric, AlertSeverity
from analytics.monitoring.alerting import AlertingEngine

logger = logging.getLogger(__name__)

class DriftEngine:
    def __init__(self, db: Session):
        self.db = db
        self.alerting = AlertingEngine(db)
        
    def calculate_psi(self, expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
        """
        Calculate Population Stability Index (PSI)
        """
        if len(expected) == 0 or len(actual) == 0:
            return 0.0
            
        # Determine bins from expected distribution
        breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
        
        expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
        actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)
        
        # Replace 0s with small value to avoid division by zero
        expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
        actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
        
        psi_value = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
        return float(psi_value)

    def calculate_ks(self, expected: np.ndarray, actual: np.ndarray) -> float:
        """
        Calculate Kolmogorov-Smirnov (KS) statistic.
        Returns the maximum distance between the CDFs.
        """
        if len(expected) == 0 or len(actual) == 0:
            return 0.0
            
        from scipy.stats import ks_2samp
        statistic, _ = ks_2samp(expected, actual)
        return float(statistic)

    def evaluate_feature_drift(self, feature_name: str, feature_version: str, 
                               expected: np.ndarray, actual: np.ndarray, 
                               ref_start: datetime, ref_end: datetime,
                               curr_start: datetime, curr_end: datetime,
                               method: str = "PSI", threshold: float = 0.2) -> FeatureDriftMetric:
                               
        if method == "PSI":
            value = self.calculate_psi(expected, actual)
        elif method == "KS":
            value = self.calculate_ks(expected, actual)
        else:
            raise ValueError(f"Unknown drift method: {method}")
            
        status = "DRIFTED" if value > threshold else "OK"
        
        metric = FeatureDriftMetric(
            feature=feature_name,
            feature_version=feature_version,
            reference_period_start=ref_start,
            reference_period_end=ref_end,
            current_period_start=curr_start,
            current_period_end=curr_end,
            metric=method,
            value=value,
            threshold=threshold,
            status=status,
            calculated_at=datetime.utcnow()
        )
        self.db.add(metric)
        self.db.commit()
        
        if status == "DRIFTED":
            severity = AlertSeverity.CRITICAL if value > threshold * 1.5 else AlertSeverity.WARNING
            self.alerting.generate_alert(
                metric=f"drift_{feature_name}",
                observed_value=value,
                threshold=threshold,
                source="DRIFT",
                severity=severity,
                message=f"Feature {feature_name} has drifted ({method}: {value:.4f} > {threshold})"
            )
        else:
            self.alerting.resolve_alert(f"drift_{feature_name}", "DRIFT")
            
        return metric
