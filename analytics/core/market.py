import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from backend.app.models.warehouse import MarketPrice, AnalyticalMarket
from analytics.contracts import MarketContract
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger(__name__)

class MarketAnalytics:
    def __init__(self, db: Session):
        self.db = db

    def prepare_symbol(self, symbol: str) -> bool:
        """
        Extracts raw market prices for a symbol, transforms into analytical features,
        validates via contract, and saves back to the analytical layer.
        """
        logger.info(f"Preparing market analytics for {symbol}")
        
        # 1. Extract
        query = self.db.query(MarketPrice).filter(MarketPrice.symbol == symbol).order_by(MarketPrice.timestamp.asc())
        df = pd.read_sql(query.statement, self.db.bind)
        
        if df.empty:
            logger.warning(f"No market data found for {symbol}")
            return False

        # 2. Transform (Ensure chronological sort to prevent leakage)
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        # Calculate daily returns (percentage change)
        df["daily_return"] = df["close"].pct_change()
        
        # Calculate log returns
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))
        
        # Calculate rolling volumes
        df["rolling_7d_volume"] = df["volume"].rolling(window=7, min_periods=1).mean()
        df["rolling_30d_volume"] = df["volume"].rolling(window=30, min_periods=1).mean()
        
        # Calculate drawdowns (from cumulative max)
        cumulative_max = df["close"].cummax()
        df["drawdown"] = (df["close"] - cumulative_max) / cumulative_max

        # 3. Validate & Upsert
        records = []
        for _, row in df.iterrows():
            try:
                # Validate against contract (handles nan to None conversions etc if configured, 
                # but we'll do explicit conversion here to avoid pydantic issues with NaN)
                
                def clean_float(val):
                    return None if pd.isna(val) else float(val)

                contract = MarketContract(
                    source=row["source_id"],
                    symbol=row["symbol"],
                    original_timestamp=row["timestamp"],
                    close=float(row["close"]),
                    volume=int(row["volume"]),
                    daily_return=clean_float(row["daily_return"]),
                    log_return=clean_float(row["log_return"]),
                    rolling_7d_volume=clean_float(row["rolling_7d_volume"]),
                    rolling_30d_volume=clean_float(row["rolling_30d_volume"]),
                    drawdown=clean_float(row["drawdown"])
                )
                
                records.append({
                    "symbol": contract.symbol,
                    "original_timestamp": contract.original_timestamp,
                    "close": contract.close,
                    "volume": contract.volume,
                    "daily_return": contract.daily_return,
                    "log_return": contract.log_return,
                    "rolling_7d_volume": contract.rolling_7d_volume,
                    "rolling_30d_volume": contract.rolling_30d_volume,
                    "drawdown": contract.drawdown,
                    "source": contract.source,
                    "transformation_timestamp": contract.transformation_timestamp,
                    "dataset_version": contract.dataset_version
                })
            except Exception as e:
                logger.error(f"Contract validation failed for {symbol} at {row['timestamp']}: {e}")
                
        if records:
            stmt = insert(AnalyticalMarket).values(records)
            upsert = stmt.on_conflict_do_update(
                constraint="uix_analytical_market",
                set_={
                    "close": stmt.excluded.close,
                    "daily_return": stmt.excluded.daily_return,
                    "log_return": stmt.excluded.log_return,
                    "rolling_7d_volume": stmt.excluded.rolling_7d_volume,
                    "rolling_30d_volume": stmt.excluded.rolling_30d_volume,
                    "drawdown": stmt.excluded.drawdown,
                    "transformation_timestamp": stmt.excluded.transformation_timestamp
                }
            )
            self.db.execute(upsert)
            self.db.commit()
            
        logger.info(f"Processed {len(records)} analytical market records for {symbol}")
        return True
