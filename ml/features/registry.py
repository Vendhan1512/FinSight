import logging
from typing import Dict, List, Any

from ml.features.validation.contracts import FeatureDefinitionContract
from ml.features.technical.definitions import TECHNICAL_FEATURES
from ml.features.technical.engine import TechnicalFeatureEngine

from ml.features.volatility.definitions import VOLATILITY_FEATURES
from ml.features.volatility.engine import VolatilityFeatureEngine

from ml.features.volume.definitions import VOLUME_FEATURES
from ml.features.volume.engine import VolumeFeatureEngine

from ml.features.fundamental.definitions import FUNDAMENTAL_FEATURES
from ml.features.fundamental.engine import FundamentalFeatureEngine

from ml.features.macro.definitions import MACRO_FEATURES
from ml.features.macro.engine import MacroFeatureEngine

from ml.features.cross_sectional.definitions import CROSS_SECTIONAL_FEATURES
from ml.features.cross_sectional.engine import CrossSectionalFeatureEngine

logger = logging.getLogger(__name__)

class FeatureSetSpec:
    def __init__(self, name: str, version: str, definitions: List[FeatureDefinitionContract], engine_class: Any):
        self.name = name
        self.version = version
        self.definitions = {d.feature_name: d for d in definitions}
        self.engine_class = engine_class

class FeatureRegistry:
    """
    Central registry for all FinSight feature sets.
    Removes hardcoded dependencies from the orchestration layer.
    """
    def __init__(self):
        self._registry: Dict[str, FeatureSetSpec] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register_set("technical", "v1", TECHNICAL_FEATURES, TechnicalFeatureEngine)
        self.register_set("risk", "v1", VOLATILITY_FEATURES, VolatilityFeatureEngine)
        self.register_set("volume", "v1", VOLUME_FEATURES, VolumeFeatureEngine)
        self.register_set("fundamental", "v1", FUNDAMENTAL_FEATURES, FundamentalFeatureEngine)
        self.register_set("macro", "v1", MACRO_FEATURES, MacroFeatureEngine)
        self.register_set("cross_sectional", "v1", CROSS_SECTIONAL_FEATURES, CrossSectionalFeatureEngine)

    def register_set(self, name: str, version: str, definitions: List[FeatureDefinitionContract], engine_class: Any):
        key = f"{name}_{version}"
        self._registry[key] = FeatureSetSpec(name, version, definitions, engine_class)
        logger.debug(f"Registered Feature Set: {key} ({len(definitions)} features)")

    def get_feature_set(self, key: str) -> FeatureSetSpec:
        if key not in self._registry:
            raise KeyError(f"Feature set '{key}' not found in registry.")
        return self._registry[key]
        
    def list_feature_sets(self) -> List[str]:
        return list(self._registry.keys())

    def get_lineage(self, feature_name: str) -> Dict[str, Any]:
        """
        Calculates the complete dependency graph for a requested feature.
        """
        for key, spec in self._registry.items():
            if feature_name in spec.definitions:
                contract = spec.definitions[feature_name]
                return {
                    "feature_name": contract.feature_name,
                    "feature_set": key,
                    "version": contract.version_tag,
                    "status": contract.status,
                    "source_dataset": contract.source_dataset,
                    "source_columns": contract.source_columns,
                    "transformation_formula": contract.formula,
                    "availability_rule": f"Must be <= Prediction Time. Frequency: {contract.frequency.value}"
                }
        raise ValueError(f"Feature '{feature_name}' not found in any registered set.")
