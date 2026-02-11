import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
import random

class NSEScraper:
    """Scrape NSE India corporate filings and insider trading data"""
    
    BASE_URL = "https://www.nseindia.com"
    
    # Critical: NSE requires these headers to avoid blocking
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.nseindia.com/",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        # First request to get cookies
        try:
            self.session.get(self.BASE_URL, timeout=10)
        except Exception as e:
            print(f"Warning: Failed to initialize NSE session: {e}")
        time.sleep(2)
    
    def get_insider_trading(self, days_back: int = 1) -> List[Dict]:
        """
        Fetch insider trading data from NSE PIT (Prohibition of Insider Trading) filings
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of insider trading records
        """
        url = f"{self.BASE_URL}/api/corporates-pit"
        
        params = {
            "index": "equities",
            "from_date": (datetime.now() - timedelta(days=days_back)).strftime("%d-%m-%Y"),
            "to_date": datetime.now().strftime("%d-%m-%Y")
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Parse and structure the data
            insider_trades = []
            for record in data.get("data", []):
                insider_trades.append({
                    "symbol": record.get("symbol"),
                    "company": record.get("company"),
                    "person": record.get("anex"),  # Acquirer/seller name
                    "category": record.get("acqName"),  # Promoter, KMP, etc.
                    "transaction_type": record.get("tdpTransactionType"),  # Buy/Sell
                    "securities_held_before": self._parse_number(record.get("befAcqSharesNo")),
                    "securities_acquired": self._parse_number(record.get("acqSharesNo")),
                    "securities_held_after": self._parse_number(record.get("afterAcqSharesNo")),
                    "percentage_before": self._parse_float(record.get("befAcqSharesPer")),
                    "percentage_after": self._parse_float(record.get("afterAcqSharesPer")),
                    "intimation_date": record.get("intimDate"),
                    "broadcast_date": record.get("xbrl"),
                    "raw_data": record
                })
            
            return insider_trades
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching insider trading data: {e}")
            return []
    
    def get_corporate_announcements(self, symbol: str = None) -> List[Dict]:
        """
        Fetch corporate announcements from NSE
        
        Args:
            symbol: Company symbol (optional, if None fetches all recent)
            
        Returns:
            List of announcements
        """
        if symbol:
            url = f"{self.BASE_URL}/api/corporate-announcements?symbol={symbol}"
        else:
            url = f"{self.BASE_URL}/api/corporate-announcements?index=equities"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            announcements = []
            for record in data.get("data", []):
                announcements.append({
                    "symbol": record.get("symbol"),
                    "company": record.get("sm_name"),
                    "subject": record.get("desc"),
                    "attachment": record.get("attchmntFile"),
                    "attachment_url": f"{self.BASE_URL}{record.get('attchmntFile')}" if record.get('attchmntFile') else None,
                    "broadcast_date": record.get("an_dt"),
                    "category": record.get("smIndustry"),
                    "raw_data": record
                })
            
            return announcements
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching corporate announcements: {e}")
            return []
    
    def get_bulk_deals(self) -> List[Dict]:
        """Fetch bulk and block deals"""
        url = f"{self.BASE_URL}/api/snapshot-capital-market-largedeal"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            print(f"Error fetching bulk deals: {e}")
            return []
    
    def get_board_meetings(self) -> List[Dict]:
        """Fetch upcoming board meetings"""
        url = f"{self.BASE_URL}/api/corporates-board-meetings"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            print(f"Error fetching board meetings: {e}")
            return []
    
    @staticmethod
    def _parse_number(value) -> int:
        """Parse number from string, handling commas"""
        if not value:
            return 0
        try:
            val_str = str(value).replace(",", "")
            if '.' in val_str:
                return int(float(val_str))
            return int(val_str)
        except:
            return 0
    
    @staticmethod
    def _parse_float(value) -> float:
        """Parse float from string"""
        if not value:
            return 0.0
        try:
            return float(str(value).replace(",", ""))
        except:
            return 0.0
    
    def respectful_delay(self):
        """Add random delay to avoid rate limiting"""
        time.sleep(random.uniform(2, 5))
