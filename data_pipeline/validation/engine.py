from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

class Severity:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class ValidationResult:
    check_name: str
    dataset: str
    record_scope: str # E.g., specific symbol or CIK to track where it failed
    status: str # "PASSED" or "FAILED"
    severity: str
    message: str
    detected_at: datetime = None

    def __post_init__(self):
        if not self.detected_at:
            self.detected_at = datetime.utcnow()

class BaseValidator:
    def __init__(self, dataset_name: str):
        self.dataset = dataset_name
        self.results: List[ValidationResult] = []

    def log_failure(self, check_name: str, record_scope: str, severity: str, message: str):
        self.results.append(ValidationResult(
            check_name=check_name,
            dataset=self.dataset,
            record_scope=record_scope,
            status="FAILED",
            severity=severity,
            message=message
        ))

    def log_pass(self, check_name: str, record_scope: str = "all"):
        self.results.append(ValidationResult(
            check_name=check_name,
            dataset=self.dataset,
            record_scope=record_scope,
            status="PASSED",
            severity=Severity.INFO,
            message="Check passed successfully."
        ))

    def validate(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validates records. Modifies self.results.
        Returns a list of valid records (drops CRITICAL failures).
        """
        raise NotImplementedError("Subclasses must implement validate()")
