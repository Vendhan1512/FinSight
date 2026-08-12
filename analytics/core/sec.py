import pandas as pd
from sqlalchemy.orm import Session
from app.models.warehouse import FinancialFact, SECFiling, AnalyticalSEC
from analytics.contracts import SECContract
from sqlalchemy.dialects.postgresql import insert
import logging

logger = logging.getLogger(__name__)

class SECAnalytics:
    def __init__(self, db: Session):
        self.db = db

    def prepare_company(self, cik: str) -> bool:
        logger.info(f"Preparing SEC analytics for CIK {cik}")
        
        # 1. Extract
        # Join facts and filings to get fiscal_period and form_type
        query = self.db.query(
            FinancialFact.metric,
            FinancialFact.value,
            FinancialFact.end_date,
            FinancialFact.source_id,
            SECFiling.form_type
        ).join(SECFiling, FinancialFact.accession_number == SECFiling.accession_number)\
         .filter(SECFiling.cik == cik)
         
        df = pd.read_sql(query.statement, self.db.bind)
        
        if df.empty:
            logger.warning(f"No SEC data found for CIK {cik}")
            return False

        # 2. Transform (Pivot to wide format)
        # Handle duplicates by taking the latest value if multiple filings hit the same end_date/metric
        df = df.sort_values("end_date").drop_duplicates(subset=["end_date", "metric"], keep="last")
        
        wide_df = df.pivot(index=["end_date", "form_type", "source_id"], columns="metric", values="value").reset_index()
        
        records = []
        for _, row in wide_df.iterrows():
            def get_val(col):
                if col in wide_df.columns:
                    val = row[col]
                    return None if pd.isna(val) else float(val)
                return None

            is_annual = "10-K" in str(row["form_type"])
            fp = "FY" if is_annual else "Q"
            
            try:
                contract = SECContract(
                    source=row["source_id"],
                    cik=cik,
                    original_timestamp=row["end_date"],
                    revenue=get_val("Revenue"),
                    net_income=get_val("Net Income"),
                    operating_income=get_val("Operating Income"),
                    total_assets=get_val("Total Assets"),
                    total_liabilities=get_val("Total Liabilities"),
                    cash_and_equivalents=get_val("Cash and Cash Equivalents"),
                    long_term_debt=get_val("Long-Term Debt"),
                    shareholders_equity=get_val("Shareholders' Equity"),
                    fiscal_period=fp,
                    is_annual=is_annual
                )
                
                records.append(contract.model_dump())
            except Exception as e:
                logger.error(f"Contract validation failed for {cik} at {row['end_date']}: {e}")
                
        if records:
            stmt = insert(AnalyticalSEC).values(records)
            upsert = stmt.on_conflict_do_update(
                constraint="uix_analytical_sec",
                set_={k: getattr(stmt.excluded, k) for k in records[0].keys() if k not in ["cik", "original_timestamp", "dataset_version"]}
            )
            self.db.execute(upsert)
            self.db.commit()
            
        logger.info(f"Processed {len(records)} analytical SEC records for CIK {cik}")
        return True
