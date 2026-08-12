from typing import List, Dict, Any
from datetime import datetime
from .engine import BaseValidator, Severity

class MarketValidator(BaseValidator):
    def __init__(self):
        super().__init__("market_prices")

    def validate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid_records = []
        for rec in records:
            symbol = rec.get("symbol", "UNKNOWN")
            date_str = str(rec.get("timestamp", ""))
            scope = f"{symbol}@{date_str}"
            
            is_valid = True

            # Check 1: Missing Fields
            if any(rec.get(k) is None for k in ["open", "high", "low", "close", "volume"]):
                self.log_failure("missing_fields", scope, Severity.CRITICAL, "One or more OHLCV fields are missing")
                is_valid = False
            
            # Check 2: High < Low (Impossible)
            if is_valid and rec["high"] < rec["low"]:
                self.log_failure("high_less_than_low", scope, Severity.CRITICAL, f"High ({rec['high']}) is less than Low ({rec['low']})")
                is_valid = False

            # Check 3: Negative Volume
            if is_valid and rec["volume"] < 0:
                self.log_failure("negative_volume", scope, Severity.CRITICAL, f"Volume ({rec['volume']}) is negative")
                is_valid = False

            # Check 4: Stale Data (Optional check, here we just log a warning if timestamp is old, 
            # though in historical ingestion this is expected. We will skip stale check for historical bulk.)
            
            if is_valid:
                valid_records.append(rec)

        if not self.results:
            self.log_pass("market_validation_suite")
            
        return valid_records

class SecValidator(BaseValidator):
    def __init__(self):
        super().__init__("financial_facts")

    def validate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid_records = []
        for rec in records:
            accn = rec.get("accession_number", "UNKNOWN")
            concept = rec.get("concept", "UNKNOWN")
            scope = f"{accn} | {concept}"
            
            is_valid = True

            if not rec.get("end_date"):
                self.log_failure("missing_end_date", scope, Severity.CRITICAL, "Financial fact is missing an end_date")
                is_valid = False
                
            if rec.get("value") is None:
                self.log_failure("missing_value", scope, Severity.WARNING, "Financial fact has a null value")
                # We don't drop warnings
                
            if is_valid:
                valid_records.append(rec)
                
        if not self.results:
            self.log_pass("sec_validation_suite")
            
        return valid_records

class FredValidator(BaseValidator):
    def __init__(self):
        super().__init__("economic_observations")

    def validate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        valid_records = []
        for rec in records:
            series = rec.get("series_id", "UNKNOWN")
            date_str = str(rec.get("observation_date", ""))
            scope = f"{series}@{date_str}"
            
            is_valid = True

            if rec.get("value") is None:
                self.log_failure("missing_observation", scope, Severity.WARNING, "Observation value is null (expected FRED anomaly '.')")
                # We keep nulls for FRED to preserve the time series structure but flag them
                
            if is_valid:
                valid_records.append(rec)
                
        if not self.results:
            self.log_pass("fred_validation_suite")
            
        return valid_records
