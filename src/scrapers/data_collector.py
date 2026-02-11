from typing import List, Dict
from .nse_scraper import NSEScraper
from .screener_scraper import ScreenerScraper
import logging
import json

class DataCollector:
    """Orchestrates all data collection from multiple sources"""
    
    def __init__(self, postgres_manager, cache_manager):
        self.postgres = postgres_manager
        self.cache = cache_manager
        self.nse = NSEScraper()
        self.logger = logging.getLogger(__name__)
    
    def collect_daily_signals(self) -> List[Dict]:
        """
        Main method to collect all signals for the day
        
        Returns:
            List of raw signals to be processed by agents
        """
        signals = []
        
        # 1. Insider trading
        self.logger.info("Fetching insider trading data...")
        insider_trades = self.nse.get_insider_trading(days_back=1)
        for trade in insider_trades:
            signals.append({
                "signal_type": "insider_trading",
                "source": "nse",
                "data": trade,
                "priority": self._score_insider_trade(trade)
            })
        
        # 2. Corporate announcements
        self.logger.info("Fetching corporate announcements...")
        announcements = self.nse.get_corporate_announcements()
        for announcement in announcements:
            if self._is_special_situation(announcement):
                signals.append({
                    "signal_type": self._classify_announcement(announcement),
                    "source": "nse",
                    "data": announcement,
                    "priority": 5  # Default priority
                })
        
        # 3. Bulk deals
        self.logger.info("Fetching bulk deals...")
        bulk_deals = self.nse.get_bulk_deals()
        for deal in bulk_deals:
            signals.append({
                "signal_type": "bulk_deal",
                "source": "nse",
                "data": deal,
                "priority": 4
            })
        
        # 4. Board meetings
        board_meetings = self.nse.get_board_meetings()
        for meeting in board_meetings:
            if self._is_interesting_meeting(meeting):
                signals.append({
                    "signal_type": "board_meeting",
                    "source": "nse",
                    "data": meeting,
                    "priority": 3
                })
        
        # Store signals in database
        self._store_signals(signals)
        
        self.logger.info(f"Collected {len(signals)} signals")
        return sorted(signals, key=lambda x: x['priority'], reverse=True)
    
    def enrich_signal_with_fundamentals(self, signal: Dict) -> Dict:
        """
        Enrich signal with fundamental data from Screener.in
        
        Args:
            signal: Raw signal with company symbol
            
        Returns:
            Enriched signal with fundamental data
        """
        symbol = signal['data'].get('symbol')
        if not symbol:
            return signal
        
        # Check cache first
        cache_key = f"fundamentals:{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            signal['fundamentals'] = cached
            return signal
        
        # Fetch from Screener.in
        with ScreenerScraper() as scraper:
            fundamentals = scraper.get_company_data(symbol)
            if fundamentals:
                signal['fundamentals'] = fundamentals
                # Cache for 24 hours
                self.cache.set(cache_key, fundamentals, ttl=86400)
        
        return signal
    
    def _score_insider_trade(self, trade: Dict) -> int:
        """Score insider trade priority (1-10)"""
        score = 5  # Base score
        
        # Promoter buying is more interesting
        if "promoter" in trade.get('category', '').lower():
            score += 2
        
        # Buying is more interesting than selling
        if "buy" in trade.get('transaction_type', '').lower():
            score += 1
        
        # Large percentage change is interesting
        pct_change = abs(trade.get('percentage_after', 0) - trade.get('percentage_before', 0))
        if pct_change > 1.0:
            score += 2
        elif pct_change > 0.5:
            score += 1
        
        return min(score, 10)
    
    def _is_special_situation(self, announcement: Dict) -> bool:
        """Determine if announcement indicates a special situation"""
        subject = announcement.get('subject', '').lower()
        
        keywords = [
            'merger', 'amalgamation', 'demerger', 'spinoff', 'scheme of arrangement',
            'buyback', 'delisting', 'rights issue', 'preferential', 
            'nclt', 'resolution', 'restructuring', 'acquisition'
        ]
        
        return any(keyword in subject for keyword in keywords)
    
    def _classify_announcement(self, announcement: Dict) -> str:
        """Classify announcement type"""
        subject = announcement.get('subject', '').lower()
        
        if any(word in subject for word in ['merger', 'amalgamation']):
            return 'merger_arb'
        elif any(word in subject for word in ['demerger', 'spinoff']):
            return 'spinoff'
        elif 'buyback' in subject:
            return 'buyback'
        elif 'delisting' in subject:
            return 'delisting'
        elif any(word in subject for word in ['rights', 'preferential', 'qip']):
            return 'capital_raise'
        elif 'nclt' in subject:
            return 'distressed_debt'
        else:
            return 'corporate_action'
    
    def _is_interesting_meeting(self, meeting: Dict) -> bool:
        """Filter for interesting board meeting purposes"""
        purpose = meeting.get('purpose', '').lower()
        
        interesting_keywords = [
            'buyback', 'dividend', 'split', 'bonus', 'merger', 'acquisition',
            'fundraise', 'rights', 'preferential'
        ]
        
        return any(keyword in purpose for keyword in interesting_keywords)
    

    def _store_signals(self, signals: List[Dict]):
        """Store signals in database for tracking"""
        for signal in signals:
            self.postgres.execute("""
                INSERT INTO signals (signal_type, company_symbol, raw_data, discovered_at)
                VALUES (%s, %s, %s, NOW())
            """, (
                signal['signal_type'],
                signal['data'].get('symbol'),
                json.dumps(signal, default=str)
            ))
