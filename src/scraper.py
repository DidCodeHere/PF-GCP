import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from typing import List
from .models import Property
import time
import random
import re

class Scraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()

    def get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }

    def search_rightmove(self, location: str, radius: float, max_price: int = 100000) -> List[Property]:
        print(f"[*] Searching Rightmove for {location} (<£{max_price})...")
        
        # 1. Resolve Location Identifier
        # This is a simplified approach. Ideally we use their autocomplete API.
        # For this demo, we'll try to get the redirect from a search.
        location_id = self._get_rightmove_location_id(location)
        if not location_id:
            print(f"[!] Could not resolve location '{location}'.")
            return []

        properties = []
        
        # 2. Construct URL
        # radius in miles.
        base_url = "https://www.rightmove.co.uk/property-for-sale/find.html"
        params = {
            'locationIdentifier': location_id,
            'maxPrice': max_price,
            'radius': radius,
            'sortType': 1, # Cheapest first
            'propertyTypes': '',
            'includeSSTC': 'false',
            'mustHave': '',
            'dontShow': '',
            'furnishTypes': '',
            'keywords': ''
        }
        
        try:
            # We might need to iterate pages. For now, just page 1 (24 results).
            response = self.session.get(base_url, params=params, headers=self.get_headers())
            if response.status_code != 200:
                print(f"[!] Error fetching Rightmove: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Select property cards
            cards = soup.find_all('div', class_='propertyCard-wrapper')
            
            for card in cards:
                try:
                    # Extract ID
                    # Some cards are featured/ads, might differ
                    anchor = card.find('a', class_='propertyCard-link')
                    if not anchor:
                        continue
                        
                    prop_id = anchor.get('href', '').split('/')[-1].replace('.html', '')
                    if not prop_id or 'channel' in prop_id: # skip ads
                        continue

                    # Title/Address
                    title_el = card.find('h2', class_='propertyCard-title')
                    title = title_el.text.strip() if title_el else "Unknown Title"
                    
                    addr_el = card.find('address', class_='propertyCard-address')
                    address = addr_el.text.strip() if addr_el else "Unknown Address"
                    
                    # Price
                    price_el = card.find('div', class_='propertyCard-priceValue')
                    price_str = price_el.text.strip() if price_el else "0"
                    price = self._parse_price(price_str)
                    
                    # Desc
                    desc_el = card.find('span', {'itemprop': 'description'})
                    description = desc_el.text.strip() if desc_el else ""
                    
                    # URL
                    url = f"https://www.rightmove.co.uk{anchor.get('href')}"
                    
                    prop = Property(
                        id=prop_id,
                        title=title,
                        address=address,
                        price=price,
                        url=url,
                        description=description,
                        tenure="Unknown" # Need to visit detail page for this usually
                    )
                    
                    # Optimization: If we want full details (Freehold check), we must visit the page.
                    # This slows it down significantly. For MVP, we rely on summary description.
                    # Or we can do it for the top X results.
                    
                    properties.append(prop)
                    
                except Exception as e:
                    # print(f"Error parsing card: {e}")
                    continue
                    
        except Exception as e:
            print(f"[!] Scraper Error: {e}")
            
        return properties

    def _get_rightmove_location_id(self, location: str) -> str:
        # Hacky way to get the REGION^XXXX code
        # We query the typeahead api
        try:
            url = f"https://www.rightmove.co.uk/typeAhead/uknostreet/GE/{location.upper()[:2]}/{location.upper()}.json"
            resp = self.session.get(url, headers=self.get_headers())
            data = resp.json()
            if data and 'typeAheadLocations' in data:
                return data['typeAheadLocations'][0]['locationIdentifier']
        except:
            pass
        return None

    def _parse_price(self, price_str: str) -> float:
        try:
            # Remove £, ,, and POA
            clean = re.sub(r'[^\d]', '', price_str)
            return float(clean) if clean else 0.0
        except:
            return 0.0
