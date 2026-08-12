import os
from .config import settings

def patch_settings_for_validate():
    """Temporarily load secrets to pass validate check in tests"""
    settings.jwt_secret_key = "secure_production_key"
    settings.alpha_vantage_api_key = "mock_key"
    settings.fred_api_key = "mock_key"
