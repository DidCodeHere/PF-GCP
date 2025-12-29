import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import time
import random
from typing import Optional, Dict, List, Any
from datetime import datetime

class MarketDataEnricher:
    def __init__(self, cache: Optional[Dict[str, Any]] = None):
        self.cache = cache if cache is not None else {}
        self.cache_expiry_days = 7
        self.semaphore = asyncio.Semaphore(2) # Limit concurrent tabs to 2 to save memory

    def get_outcode(self, address: str) -> Optional[str]:
        """Extracts the UK outcode (first part of postcode) from an address string."""
        if not address:
            return None
        matches = re.findall(r'\b([A-Z]{1,2}[0-9][0-9A-Z]?)\b', address.upper())
        if matches:
            return matches[-1]
        return None

    async def fetch_all_stats(self, outcodes: List[str]) -> None:
        """Fetches stats for a list of outcodes using Playwright."""
        
        # Filter outcodes that need updating
        to_fetch = []
        for outcode in outcodes:
            if not outcode: continue
            
            needs_update = True
            if outcode in self.cache:
                entry = self.cache[outcode]
                # Check if data is missing (null) or expired
                is_missing_data = (entry.get('avg_price') is None or entry.get('avg_rent') is None)
                
                if 'timestamp' in entry and not is_missing_data:
                    age_days = (datetime.now().timestamp() - entry['timestamp']) / 86400
                    if age_days < self.cache_expiry_days:
                        needs_update = False
            
            if needs_update:
                to_fetch.append(outcode)

        if not to_fetch:
            return

        print(f"  > Enricher: {len(to_fetch)} areas need updating. Launching browser...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Process in chunks to avoid opening too many tabs
            chunk_size = 5
            for i in range(0, len(to_fetch), chunk_size):
                chunk = to_fetch[i:i + chunk_size]
                # Pass browser, not context
                tasks = [self._process_outcode(browser, outcode) for outcode in chunk]
                await asyncio.gather(*tasks)
                
            await browser.close()

    async def _process_outcode(self, browser, outcode: str):
        """Fetches data for a single outcode using a new page."""
        async with self.semaphore:
            # Add a small random delay to avoid burst patterns
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
            # Create a fresh context for each request to avoid shared state detection
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            try:
                print(f"  > Fetching market data for {outcode}...")
                
                # Retry logic for price
                price = None
                for attempt in range(2):
                    price = await self._fetch_avg_price(page, outcode)
                    if price is not None:
                        break
                    if attempt == 0:
                        print(f"    ! Retrying price for {outcode}...")
                        await asyncio.sleep(2)

                # Retry logic for rent
                rent = None
                for attempt in range(2):
                    rent = await self._fetch_avg_rent(page, outcode)
                    if rent is not None:
                        break
                    if attempt == 0:
                        print(f"    ! Retrying rent for {outcode}...")
                        await asyncio.sleep(2)
                
                self.cache[outcode] = {
                    'avg_price': price,
                    'avg_rent': rent,
                    'timestamp': datetime.now().timestamp()
                }
            except Exception as e:
                print(f"    ! Error processing {outcode}: {e}")
            finally:
                await page.close()
                await context.close()

    async def _fetch_avg_price(self, page, outcode: str) -> Optional[float]:
        """Scrapes Zoopla for average sold price."""
        url = f"https://www.zoopla.co.uk/house-prices/{outcode}/"
        try:
            await page.goto(url, timeout=15000)
            
            # Handle cookie consent if it appears (Zoopla often has one)
            try:
                # Quick check for common cookie buttons
                await page.locator("button:has-text('Accept all')").click(timeout=1000)
            except:
                pass

            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()
            
            match = re.search(r"average sold price.*?£([\d,]+)", text, re.IGNORECASE | re.DOTALL)
            if match:
                return float(match.group(1).replace(',', ''))
            
            # Fallback: Look for specific header
            # "The average sold price for a property in L1 in the last 12 months is £134,233"
            # Sometimes the text is split.
            
        except Exception as e:
            print(f"    ! Error fetching price for {outcode}: {e}")
            pass
        return None

    async def _fetch_avg_rent(self, page, outcode: str) -> Optional[float]:
        """Scrapes Home.co.uk for average rent."""
        # Note: Home.co.uk is sensitive to exact outcode format. 
        # Try to ensure it's uppercase.
        url = f"https://www.home.co.uk/rental-prices/postcode/{outcode}/current"
        try:
            await page.goto(url, timeout=15000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()
            
            match = re.search(r"Average rent.*?£([\d,]+)", text, re.IGNORECASE | re.DOTALL)
            if match:
                return float(match.group(1).replace(',', ''))
        except Exception as e:
            print(f"    ! Error fetching rent for {outcode}: {e}")
            pass
        return None

    def get_cached_stats(self, outcode: str) -> Dict[str, Optional[float]]:
        """Returns stats from cache (assumes fetch_all_stats has run)."""
        if outcode in self.cache:
            entry = self.cache[outcode]
            return {
                'avg_price': entry.get('avg_price'),
                'avg_rent': entry.get('avg_rent')
            }
        return {'avg_price': None, 'avg_rent': None}

    def get_cached_stats(self, outcode: str) -> Dict[str, Optional[float]]:
        """Returns stats from cache (assumes fetch_all_stats has run)."""
        if outcode in self.cache:
            entry = self.cache[outcode]
            return {
                'avg_price': entry.get('avg_price'),
                'avg_rent': entry.get('avg_rent')
            }
        return {'avg_price': None, 'avg_rent': None}
