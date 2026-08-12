import pandas as pd
from sqlalchemy.orm import Session
from app.models.warehouse import EconomicObservation, AnalyticalFRED
from analytics.contracts import FREDContract
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger(__name__)

class FREDAnalytics:
    def __init__(self, db: Session):
        self.db = db

    def prepare_dataset(self) -> bool:
        logger.info(f"Preparing FRED analytics (aligned datasets)")
        
        # Extract all observations
        query = self.db.query(EconomicObservation)
        df = pd.read_sql(query.statement, self.db.bind)
        
        if df.empty:
            logger.warning("No FRED data found")
            return False

        # Drop duplicates focusing on latest realtime_start
        df = df.sort_values("realtime_start").drop_duplicates(subset=["series_id", "observation_date"], keep="last")
        
        # Pivot to wide format so each date has a column for each series
        wide_df = df.pivot(index=["observation_date", "source_id"], columns="series_id", values="value").reset_index()
        
        records = []
        for _, row in wide_df.iterrows():
            def get_val(col):
                if col in wide_df.columns:
                    val = row[col]
                    return None if pd.isna(val) else float(val)
                return None

            try:
                contract = FREDContract(
                    source=row["source_id"],
                    original_timestamp=row["observation_date"],
                    fedfunds=get_val("FEDFUNDS"),
                    cpiaucsl=get_val("CPIAUCSL"),
                    unrate=get_val("UNRATE"),
                    gdp=get_val("GDP"),
                    gs10=get_val("GS10")
                )
                records.append(contract.model_dump())
            except Exception as e:
                logger.error(f"Contract validation failed at {row['observation_date']}: {e}")
                
        if records:
            stmt = insert(AnalyticalFRED).values(records)
            upsert = stmt.on_conflict_do_update(
                constraint="uix_analytical_fred",
                set_={k: getattr(stmt.excluded, k) for k in records[0].keys() if k not in ["original_timestamp", "dataset_version"]}
            )
            self.db.execute(upsert)
            self.db.commit()
            
        logger.info(f"Processed {len(records)} analytical FRED records")
        return True
