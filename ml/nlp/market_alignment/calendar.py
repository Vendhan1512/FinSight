import logging
from datetime import datetime, timedelta, time
import pandas as pd
import pytz

logger = logging.getLogger(__name__)

class MarketCalendarAligner:
    """
    Aligns raw article publication timestamps (assumed UTC) 
    to the correct market observation window.
    
    Rules for US Equities (EST/EDT):
    - Market Hours: 09:30 to 16:00 EST.
    - Pre-market (Before 09:30): Maps to the same day's market window (if trading day).
    - Intraday (09:30 - 16:00): Maps to the same day's close.
    - Post-market (After 16:00): Maps to the NEXT trading day's window.
    - Weekends/Holidays: Maps to the NEXT trading day's window.
    """
    
    def __init__(self):
        # We will use US/Eastern to localize
        self.market_tz = pytz.timezone('US/Eastern')
        # Standard US market holidays (simplified using pandas USFederalHolidayCalendar)
        # Note: True NYSE holidays are slightly different, but this is a good proxy.
        from pandas.tseries.holiday import USFederalHolidayCalendar
        self.cal = USFederalHolidayCalendar()
        self.holidays = self.cal.holidays(start='2000-01-01', end='2050-12-31')

    def is_trading_day(self, dt: datetime) -> bool:
        """Checks if a given date is a valid trading day (weekday and not a holiday)."""
        if dt.weekday() >= 5: # 5=Sat, 6=Sun
            return False
        # Normalize to midnight for holiday check
        dt_norm = pd.Timestamp(dt.date())
        if dt_norm in self.holidays:
            return False
        return True

    def get_next_trading_day(self, dt: datetime) -> datetime:
        """Finds the next valid trading day strictly *after* the given date."""
        next_day = dt + timedelta(days=1)
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    def align_event(self, published_utc: datetime) -> dict:
        """
        Takes a UTC publication time. Returns the relation type and the 
        target market observation day (the day whose close will fully absorb the news).
        """
        # Ensure UTC timezone, then convert to Market Timezone
        if published_utc.tzinfo is None:
            published_utc = pytz.utc.localize(published_utc)
            
        market_time = published_utc.astimezone(self.market_tz)
        
        m_date = market_time.date()
        m_time = market_time.time()
        
        is_trading = self.is_trading_day(market_time)
        
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        if not is_trading:
            # Weekend or Holiday
            target_date = self.get_next_trading_day(market_time)
            relation = "WEEKEND_HOLIDAY"
        else:
            if m_time < market_open:
                # Pre-market
                target_date = m_date
                relation = "PRE_MARKET"
            elif m_time >= market_close:
                # Post-market
                target_date = self.get_next_trading_day(market_time).date()
                relation = "POST_MARKET"
            else:
                # Intraday
                target_date = m_date
                relation = "INTRADAY"
                
        # Return target date as datetime (midnight) for matching with analytical_market
        # which usually stores original_timestamp as midnight date representations.
        target_datetime = datetime.combine(target_date, time(0,0))
        
        return {
            "market_session_relation": relation,
            "target_observation_date": target_datetime
        }
