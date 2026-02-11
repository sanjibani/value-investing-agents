from playwright.sync_api import sync_playwright
import time
from typing import Dict, Optional

class ScreenerScraper:
    """
    Scrape Screener.in for fundamental data
    Uses Playwright for JavaScript-heavy pages
    """
    
    BASE_URL = "https://www.screener.in"
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
    
    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def get_company_data(self, symbol: str) -> Optional[Dict]:
        """
        Get comprehensive company data from Screener.in
        
        Args:
            symbol: NSE symbol (e.g., 'RELIANCE')
            
        Returns:
            Dictionary with financial metrics
        """
        page = self.context.new_page()
        
        try:
            url = f"{self.BASE_URL}/company/{symbol}/"
            page.goto(url, timeout=30000)
            time.sleep(3)  # Wait for dynamic content
            
            # Extract key metrics
            data = {
                "symbol": symbol,
                "name": self._extract_text(page, "#top h1"),
                "market_cap": self._extract_metric(page, "Market Cap"),
                "current_price": self._extract_metric(page, "Current Price"),
                "pe_ratio": self._extract_metric(page, "Stock P/E"),
                "book_value": self._extract_metric(page, "Book Value"),
                "dividend_yield": self._extract_metric(page, "Dividend Yield"),
                "roce": self._extract_metric(page, "ROCE"),
                "roe": self._extract_metric(page, "ROE"),
                "debt_to_equity": self._extract_metric(page, "Debt to equity"),
                "sales_growth_3yr": self._extract_metric(page, "Sales growth"),
                "profit_growth_3yr": self._extract_metric(page, "Profit growth"),
                "promoter_holding": self._extract_metric(page, "Promoter holding"),
                "pledged_percentage": self._extract_metric(page, "Pledged percentage")
            }
            
            return data
            
        except Exception as e:
            print(f"Error scraping {symbol}: {e}")
            return None
        finally:
            page.close()
    
    def _extract_text(self, page, selector: str) -> str:
        """Extract text from element"""
        try:
            element = page.query_selector(selector)
            return element.inner_text().strip() if element else ""
        except:
            return ""
    
    def _extract_metric(self, page, label: str) -> str:
        """Extract metric value by label"""
        try:
            # Screener.in uses specific structure for metrics
            # Try exact match first, then contains
            element = page.locator(f"li.flex:has-text('{label}') span.number").first
            return element.inner_text().strip() if element else ""
        except:
            return ""
    
    def search_companies(self, query: str) -> list:
        """Search for companies by name or symbol"""
        page = self.context.new_page()
        
        try:
            page.goto(f"{self.BASE_URL}/search/?q={query}")
            time.sleep(2)
            
            results = []
            # Parse search results
            # Implementation depends on Screener.in HTML structure
            
            return results
        finally:
            page.close()
