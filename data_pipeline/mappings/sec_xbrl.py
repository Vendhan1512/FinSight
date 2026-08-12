# Standard FinSight metrics mapped to SEC us-gaap concepts

SEC_XBRL_MAPPING = {
    "us-gaap:Revenues": "Revenue",
    "us-gaap:SalesRevenueNet": "Revenue",
    "us-gaap:SalesRevenueGoodsNet": "Revenue",
    
    "us-gaap:NetIncomeLoss": "Net Income",
    
    "us-gaap:OperatingIncomeLoss": "Operating Income",
    
    "us-gaap:Assets": "Total Assets",
    
    "us-gaap:Liabilities": "Total Liabilities",
    
    "us-gaap:CashAndCashEquivalentsAtCarryingValue": "Cash and Cash Equivalents",
    "us-gaap:Cash": "Cash and Cash Equivalents",
    
    "us-gaap:LongTermDebt": "Long-Term Debt",
    "us-gaap:LongTermDebtNoncurrent": "Long-Term Debt",
    
    "us-gaap:StockholdersEquity": "Shareholders' Equity",
    "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "Shareholders' Equity"
}

def map_concept(concept: str) -> str:
    """
    Returns the mapped internal metric name, or 'Unknown' if not mapped.
    """
    return SEC_XBRL_MAPPING.get(concept, "Unknown")
