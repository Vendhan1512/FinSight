import json
import os

ASSET_UNIVERSE = [
    {"ticker": "AAPL", "sector": "Information Technology", "name": "Apple Inc."},
    {"ticker": "JNJ", "sector": "Health Care", "name": "Johnson & Johnson"},
    {"ticker": "JPM", "sector": "Financials", "name": "JPMorgan Chase & Co."},
    {"ticker": "XOM", "sector": "Energy", "name": "Exxon Mobil Corp."},
    {"ticker": "PG", "sector": "Consumer Staples", "name": "Procter & Gamble Co."},
    {"ticker": "AMZN", "sector": "Consumer Discretionary", "name": "Amazon.com Inc."},
    {"ticker": "NEE", "sector": "Utilities", "name": "NextEra Energy Inc."},
    {"ticker": "BA", "sector": "Industrials", "name": "Boeing Co."},
    {"ticker": "NEM", "sector": "Materials", "name": "Newmont Corporation"},
    {"ticker": "SPG", "sector": "Real Estate", "name": "Simon Property Group"}
]

def get_asset_universe():
    return ASSET_UNIVERSE
