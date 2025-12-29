from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from typing import List
from .models import Property
import re
import time

class Scraper:
    def __init__(self):
        self.default_timeout = 20000 # 20 seconds

    def search_rightmove(self, location: str, radius: float, max_price: int = 100000) -> List[Property]:
        print(f"[*] Searching Rightmove for {location} (<£{max_price})...")
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(self.default_timeout)

            try:
                # 1. Resolve Location by simulating user search
                print("   Resolving location...")
                page.goto("https://www.rightmove.co.uk/", wait_until="domcontentloaded")
                
                # Handle Cookies
                try:
                    # Try different common cookie buttons
                    cookie_btn = page.locator("button:has-text('Accept all')")
                    if cookie_btn.is_visible(timeout=2000):
                        cookie_btn.click(timeout=2000)
                    else:
                        page.locator("button#onetrust-accept-btn-handler").click(timeout=2000)
                except:
                    pass

                # Type location
                # Updated selector to be more specific to "For Sale"
                search_input = page.locator("input[data-monitor-testid='for-sale-search-input']")
                if not search_input.is_visible(timeout=2000):
                     # Fallback
                     search_input = page.locator("input[name='locationSearch']").first
                
                search_input.fill(location)
                # Wait for autocomplete suggestions (sometimes required)
                page.wait_for_timeout(1000) 
                
                # Click "For Sale" button
                # Use specific button for "For Sale" search
                search_btn = page.locator("button[data-monitor-testid='for-sale-search-button']")
                if search_btn.is_visible():
                    search_btn.click()
                else:
                    # Fallback
                    page.keyboard.press("Enter")

                # Wait for navigation
                try:
                    # It might go to /property-for-sale/search.html or /property-for-sale/find.html
                    page.wait_for_url("**/property-for-sale/**", timeout=10000)
                except:
                    print(f"[!] Timeout or wrong redirect for '{location}'. URL: {page.url}")
                    return []

                current_url = page.url
                
                # Extract locationIdentifier from URL
                # format: ...?locationIdentifier=REGION%5E93917...
                match = re.search(r'locationIdentifier=([^&]+)', current_url)
                if not match:
                    print(f"[!] Could not determine locationIdentifier from {current_url}")
                    return []
                
                location_id = match.group(1)
                
                # 2. Construct precise URL with filters
                # We use the extracted location_id
                print(f"   Location ID: {location_id}")
                
                allowed_radii = [0.0, 0.25, 0.5, 1.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0]
                chosen_radius = min(allowed_radii, key=lambda x: abs(x - radius))

                base_url = "https://www.rightmove.co.uk/property-for-sale/find.html"
                url = (
                    f"{base_url}?"
                    f"locationIdentifier={location_id}&"
                    f"maxPrice={max_price}&"
                    f"radius={chosen_radius}&"
                    f"sortType=1&"
                    f"propertyTypes=&"
                    f"includeSSTC=false&"
                    f"mustHave=&"
                    f"dontShow=&"
                    f"furnishTypes=&"
                    f"keywords="
                )
                
                print(f"   Fetching results...")
                page.goto(url, wait_until="load")
                
                # Wait a bit for any dynamic content
                page.wait_for_timeout(2000)

                # 3. Parse content
                import json
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                script_tag = soup.find('script', id='__NEXT_DATA__')
                
                if not script_tag:
                    print("[!] Could not find __NEXT_DATA__ script tag")
                    return []
                
                data = json.loads(script_tag.string)
                try:
                    results = data['props']['pageProps']['searchResults']['properties']
                except KeyError:
                    print("[!] Could not find properties in __NEXT_DATA__")
                    return []
                
                properties = []
                for p_data in results:
                    try:
                        prop_id = str(p_data.get('id'))
                        address = p_data.get('displayAddress', 'Unknown Address')
                        title = p_data.get('propertyTypeFullDescription', 'Property')
                        price = float(p_data.get('price', {}).get('amount', 0))
                        
                        # Handle summary/description
                        description = p_data.get('summary', '')
                        
                        # Rightmove usually has tenure in tenure.tenureType
                        tenure = p_data.get('tenure', {}).get('tenureType', 'Unknown')
                        
                        # Agent name
                        agent = p_data.get('customer', {}).get('branchDisplayName', 'Unknown')
                        
                        href = p_data.get('propertyUrl', f"/properties/{prop_id}")
                        url = f"https://www.rightmove.co.uk{href}"
                        
                        prop = Property(
                            id=prop_id,
                            title=title,
                            address=address,
                            price=price,
                            url=url,
                            description=description,
                            tenure=tenure,
                            agent=agent
                        )
                        properties.append(prop)
                        
                    except Exception as e:
                        continue
                
                print(f"   Found {len(properties)} properties.")
                return properties

            except Exception as e:
                print(f"[!] Scraper Error: {e}")
                return []
            finally:
                browser.close()

    def search_auction_house(self, location: str, radius: float, max_price: int = 100000) -> List[Property]:
        """
        Scrapes Auction House UK for properties.
        """
        print(f"[*] Searching Auction House UK for {location}...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(self.default_timeout)

            try:
                # Use the search URL that works: /auction/search-results?keyword=Location
                base_url = "https://www.auctionhouse.co.uk/auction/search-results"
                url = f"{base_url}?keyword={location}"
                
                print(f"   Navigating to {url}...")
                page.goto(url, wait_until="domcontentloaded")
                
                try:
                    page.locator("button:has-text('Allow all cookies')").click(timeout=2000)
                except:
                    pass
                    
                page.wait_for_timeout(2000)
                
                # Parse results using a more specific selector to avoid iterating thousands of links
                # We look for the container of results first
                # Debug showed: <div class="col-sm-12 col-md-8 col-lg-6 text-center lot-search-result">
                
                # Wait for at least one result or timeout
                try:
                    page.wait_for_selector(".lot-search-result", timeout=5000)
                except:
                    print("   [!] No results found or timeout waiting for results.")
                    return []

                # Get links only within the result cards
                links = page.locator(".lot-search-result a.home-lot-wrapper-link").all()
                
                properties = []
                # Limit to first 50 to prevent hanging if there are too many
                for link in links[:50]:
                    try:
                        href = link.get_attribute("href")
                        if not href: continue
                        
                        # Handle relative URLs if any (though debug showed absolute)
                        if href.startswith("/"):
                            url = f"https://www.auctionhouse.co.uk{href}"
                        else:
                            url = href
                            
                        prop_id = url.split("/")[-1]
                        
                        # Get the card content (parent div)
                        text_content = link.inner_text()
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        
                        price = 0.0
                        price_text = "POA"
                        title = "Auction Property"
                        address = "Unknown Address"
                        
                        for line in lines:
                            if "£" in line:
                                price_text = line
                                price = self._parse_price(line)
                            elif "Bed" in line or "Land" in line or "Property" in line:
                                title = line
                            elif len(line) > 10 and "£" not in line and "Lot" not in line:
                                address = line
                        
                        if address == "Unknown Address" and lines:
                            address = lines[-1]

                        if price > 0 and price > max_price:
                            continue
                            
                        prop = Property(
                            id=prop_id,
                            title=title,
                            address=address,
                            price=price if price > 0 else None,
                            url=url,
                            description=text_content,
                            tenure="Unknown",
                            agent="Auction House UK",
                            price_display=price_text
                        )
                        properties.append(prop)
                        
                    except Exception as e:
                        continue
                
                print(f"   Found {len(properties)} properties on Auction House UK.")
                return properties

            except Exception as e:
                print(f"[!] Auction House Scraper Error: {e}")
                return []
            finally:
                browser.close()

    def search_zoopla(self, location: str, radius: float, max_price: int = 100000) -> List[Property]:
        print(f"[*] Searching Zoopla for {location} (<£{max_price})...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(self.default_timeout)

            try:
                # Zoopla URL construction
                # location needs to be slugified usually, but let's try the search box first if needed, 
                # or just direct URL injection which Zoopla handles well.
                
                # Zoopla uses 'station' or 'postcode' or 'area' in the path.
                # e.g. https://www.zoopla.co.uk/for-sale/property/manchester/?price_max=100000&radius=5
                
                base_url = f"https://www.zoopla.co.uk/for-sale/property/{location}/"
                url = f"{base_url}?price_max={max_price}&radius={radius}&results_sort=lowest_price&page_size=25"
                
                print(f"   Navigating to {url}...")
                page.goto(url, wait_until="domcontentloaded")
                
                # Handle cookies
                try:
                    page.locator("button:has-text('Accept all cookies')").click(timeout=2000)
                except:
                    pass
                
                page.wait_for_timeout(2000)
                
                # Parse results
                # Zoopla classes change frequently. We might need to rely on more generic selectors or JSON data if available.
                # Zoopla often embeds JSON in a script tag with id="__NEXT_DATA__" just like Rightmove.
                
                import json
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                script_tag = soup.find('script', id='__NEXT_DATA__')
                
                properties = []
                
                if script_tag:
                    try:
                        data = json.loads(script_tag.string)
                        # Path to listings might vary. 
                        # Usually: props -> pageProps -> regularListingsFormatted
                        listings = data.get('props', {}).get('pageProps', {}).get('regularListingsFormatted', [])
                        
                        for p_data in listings:
                            try:
                                prop_id = str(p_data.get('listingId'))
                                address = p_data.get('address', 'Unknown Address')
                                title = p_data.get('title', 'Property')
                                price_str = p_data.get('price', '0')
                                price = self._parse_price(price_str)
                                
                                # Description might be short or missing in this JSON
                                description = title + " " + p_data.get('features', '') # Features is sometimes a list
                                if isinstance(p_data.get('features'), list):
                                    description += " ".join(p_data.get('features'))
                                
                                # Construct URL
                                link = p_data.get('transports', {}).get('detailsUrl') # This seems wrong, let's check standard fields
                                # Usually there is a 'uris' or similar.
                                # Let's fallback to constructing it.
                                url = f"https://www.zoopla.co.uk/for-sale/details/{prop_id}"
                                
                                prop = Property(
                                    id=prop_id,
                                    title=title,
                                    address=address,
                                    price=price,
                                    url=url,
                                    description=description,
                                    tenure="Unknown", # Zoopla JSON often doesn't have tenure in the list view
                                    agent=p_data.get('branch', {}).get('name', 'Unknown')
                                )
                                properties.append(prop)
                            except Exception as e:
                                continue
                    except Exception as e:
                        print(f"[!] Error parsing Zoopla JSON: {e}")
                
                # Fallback to HTML parsing if JSON fails or is empty
                if not properties:
                    print("   JSON parsing failed or empty. Trying HTML parsing...")
                    cards = page.locator("div[data-testid='regular-listings'] div[id^='listing_']").all()
                    
                    for card in cards:
                        try:
                            prop_id = card.get_attribute("id").replace("listing_", "")
                            
                            # Price
                            price_el = card.locator("p[data-testid='listing-price']")
                            if price_el.count():
                                price_str = price_el.inner_text()
                            else:
                                # Fallback for price
                                price_str = "0"
                            
                            price = self._parse_price(price_str)
                            
                            # Address
                            address_el = card.locator("address")
                            if address_el.count():
                                address = address_el.inner_text()
                            else:
                                address = "Unknown Address"
                            
                            # Title - Zoopla seems to have removed the clear title (e.g. "2 bed flat") from some views
                            # We will try to construct it from features or use address
                            title = "Property"
                            # Try to find bed/bath info
                            text_content = card.inner_text()
                            # Simple heuristic to find "X beds"
                            beds_match = re.search(r'(\d+\s+beds?)', text_content, re.IGNORECASE)
                            if beds_match:
                                title = f"{beds_match.group(1)} property"
                            
                            # Link
                            # Find the link that goes to details
                            link_el = card.locator("a[href^='/for-sale/details/']").first
                            if link_el.count():
                                link = link_el.get_attribute("href")
                                url = f"https://www.zoopla.co.uk{link}"
                            else:
                                # Fallback
                                link_el = card.locator("a").first
                                link = link_el.get_attribute("href")
                                url = f"https://www.zoopla.co.uk{link}"
                            
                            prop = Property(
                                id=prop_id,
                                title=title,
                                address=address,
                                price=price,
                                url=url,
                                description=text_content, # Use full card text as description for now
                                tenure="Unknown",
                                agent="Unknown"
                            )
                            properties.append(prop)
                        except Exception as e:
                            # print(f"Error parsing card: {e}")
                            continue

                print(f"   Found {len(properties)} properties on Zoopla.")
                return properties

            except Exception as e:
                print(f"[!] Zoopla Scraper Error: {e}")
                return []
            finally:
                browser.close()

    def search_pugh(self, location: str, radius: float, max_price: int = 100000) -> List[Property]:
        """
        Scrapes Pugh & Co Auctions.
        """
        print(f"[*] Searching Pugh Auctions for {location} (Radius: {radius}m)...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(self.default_timeout)

            try:
                # Use direct search URL with parameters
                # Pugh radius seems to be in miles.
                # URL seen in debug: property-search?location=Liverpool&property-type=&radius=3...
                
                # Map our radius to Pugh's likely allowed values if needed, or just pass it.
                # Let's assume it takes an integer or float.
                
                url = f"https://www.pugh-auctions.com/property-search?location={location}&radius={radius}&include-sold=off"
                
                print(f"   Navigating to {url}...")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
                
                # Parse results
                # Look for links containing /property/ or /lot/
                links = page.locator("a[href*='/property/']").all()
                
                properties = []
                seen_ids = set()
                
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        if not href: continue
                        
                        prop_id = href.split("/")[-1]
                        if prop_id in seen_ids:
                            continue
                        seen_ids.add(prop_id)
                        
                        url = f"https://www.pugh-auctions.com{href}"
                        
                        # Get card text from parent
                        # Link is usually inside the card or wraps it?
                        # Debug showed link is separate?
                        # "First link: https://www.pugh-auctions.com/property/37635"
                        # "Card Text: 067 VIEW PROPERTY FLAT 408..."
                        # So we need to find the container.
                        # Let's assume the link is inside the container.
                        card = link.locator("..").locator("..")
                        text_content = card.inner_text()
                        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                        
                        price = 0.0
                        price_text = "POA"
                        address = "Unknown Address"
                        title = "Auction Property"
                        
                        # Parse text
                        # FLAT 408... (Address)
                        # Guide Price: £25,000 plus
                        
                        for line in lines:
                            if "Guide Price" in line or "£" in line:
                                price_text = line
                                price = self._parse_price(line)
                            elif "," in line and len(line) > 15:
                                # Address heuristic
                                address = line
                        
                        # Filter
                        if price > 0 and price > max_price:
                            continue
                            
                        prop = Property(
                            id=prop_id,
                            title=title,
                            address=address,
                            price=price if price > 0 else None,
                            url=url,
                            description=text_content,
                            tenure="Unknown",
                            agent="Pugh Auctions",
                            price_display=price_text
                        )
                        properties.append(prop)
                        
                    except Exception as e:
                        continue
                
                print(f"   Found {len(properties)} properties on Pugh Auctions.")
                return properties

            except Exception as e:
                print(f"[!] Pugh Scraper Error: {e}")
                return []
            finally:
                browser.close()

    def _parse_price(self, price_str: str) -> float:
        try:
            clean = re.sub(r'[^\d]', '', price_str)
            return float(clean) if clean else 0.0
        except:
            return 0.0

    def search_nestoria(self, location: str, radius: float, max_price: int = 100000) -> List[Property]:
        """
        Search Nestoria using their public API.
        
        Nestoria has a confirmed free API at api.nestoria.co.uk
        Docs: https://www.nestoria.co.uk/help/api
        
        This is a lightweight API-based scraper - no browser needed!
        """
        import httpx
        import ssl
        
        print(f"[*] Searching Nestoria API for {location} (<£{max_price})...")
        
        properties = []
        
        try:
            # Nestoria API endpoint
            base_url = "https://api.nestoria.co.uk/api"
            
            # Convert radius from miles to km (Nestoria uses km)
            radius_km = radius * 1.60934
            
            params = {
                "action": "search_listings",
                "country": "uk",
                "encoding": "json",
                "listing_type": "buy",
                "place_name": location,
                "price_max": max_price,
                "number_of_results": 50,
                "sort": "price_lowhigh",
            }
            
            # Add radius if specified (Nestoria accepts radius in km)
            if radius_km > 0:
                params["radius"] = min(radius_km, 50)  # Cap at 50km
            
            # Make API request with timeout and SSL handling
            # Some older APIs have SSL issues, try with relaxed SSL first
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(base_url, params=params)
                    response.raise_for_status()
                    data = response.json()
            except (ssl.SSLError, httpx.ConnectError):
                # Fallback: try with verify=False (not ideal but Nestoria's cert may be outdated)
                print("   [!] SSL issue, retrying with relaxed verification...")
                with httpx.Client(timeout=30.0, verify=False) as client:
                    response = client.get(base_url, params=params)
                    response.raise_for_status()
                    data = response.json()
            
            # Check response status
            response_obj = data.get("response", {})
            status = response_obj.get("application_response_code", "")
            
            if status not in ["100", "101", "110"]:
                # 100 = OK, 101 = OK but no results, 110 = OK with spelling correction
                print(f"   [!] Nestoria API returned code: {status}")
                return []
            
            listings = response_obj.get("listings", [])
            
            for listing in listings:
                try:
                    prop_id = str(listing.get("lister_url", "").split("/")[-1] or listing.get("title", "")[:20])
                    
                    price = float(listing.get("price", 0))
                    if price > max_price:
                        continue
                    
                    # Format price display
                    price_display = f"£{price:,.0f}" if price > 0 else "POA"
                    price_formatted = listing.get("price_formatted", price_display)
                    
                    # Build title from property type and bedrooms
                    bedrooms = listing.get("bedroom_number", "")
                    prop_type = listing.get("property_type", "property")
                    title = f"{bedrooms} Bed {prop_type.title()}" if bedrooms else prop_type.title()
                    
                    # Description
                    summary = listing.get("summary", "")
                    title_text = listing.get("title", "")
                    description = f"{title_text}. {summary}".strip()
                    
                    prop = Property(
                        id=prop_id,
                        title=title,
                        address=listing.get("title", "Unknown Address"),
                        price=price if price > 0 else None,
                        url=listing.get("lister_url", ""),
                        description=description,
                        tenure="Unknown",
                        agent=listing.get("datasource_name", "Nestoria"),
                        price_display=price_formatted
                    )
                    properties.append(prop)
                    
                except Exception as e:
                    continue
            
            print(f"   Found {len(properties)} properties on Nestoria.")
            return properties
            
        except httpx.TimeoutException:
            print(f"[!] Nestoria API timeout")
            return []
        except httpx.HTTPStatusError as e:
            print(f"[!] Nestoria API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            print(f"[!] Nestoria API error: {e}")
            return []

    def search_onthemarket(self, location: str, radius: float, max_price: int = 100000) -> List[Property]:
        """
        Search OnTheMarket.
        
        Uses Playwright as we haven't confirmed an API yet.
        Includes timeout protection.
        """
        print(f"[*] Searching OnTheMarket for {location} (<£{max_price})...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(self.default_timeout)

            try:
                # OnTheMarket URL structure
                # https://www.onthemarket.com/for-sale/property/liverpool/?max-price=100000&radius=5
                radius_param = int(radius) if radius >= 1 else 0.5
                url = f"https://www.onthemarket.com/for-sale/property/{location.lower().replace(' ', '-')}/?max-price={max_price}&radius={radius_param}&view=grid"
                
                print(f"   Navigating to {url}...")
                page.goto(url, wait_until="domcontentloaded")
                
                # Handle cookies
                try:
                    page.locator("button:has-text('Accept all')").click(timeout=2000)
                except:
                    pass
                
                page.wait_for_timeout(2000)
                
                # Try to find JSON data first (many modern sites embed it)
                properties = []
                
                # Look for __NEXT_DATA__ or similar
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # OnTheMarket uses server-rendered HTML, parse directly
                # Property cards have class 'property-card' or similar
                cards = page.locator("[data-testid='result-card'], .otm-PropertyCard").all()
                
                if not cards:
                    # Fallback: try generic selectors
                    cards = page.locator("article, .property-result").all()
                
                for card in cards[:50]:  # Limit to 50
                    try:
                        # Extract link
                        link_el = card.locator("a[href*='/details/']").first
                        if not link_el.count():
                            link_el = card.locator("a").first
                        
                        href = link_el.get_attribute("href") if link_el.count() else None
                        if not href:
                            continue
                        
                        url = f"https://www.onthemarket.com{href}" if href.startswith("/") else href
                        prop_id = href.split("/")[-2] if "/details/" in href else href.split("/")[-1]
                        
                        # Extract text content
                        text = card.inner_text()
                        lines = [l.strip() for l in text.split('\n') if l.strip()]
                        
                        price = 0.0
                        price_display = "POA"
                        title = "Property"
                        address = "Unknown"
                        
                        for line in lines:
                            if "£" in line:
                                price_display = line
                                price = self._parse_price(line)
                            elif "bed" in line.lower():
                                title = line
                            elif "," in line and len(line) > 10:
                                address = line
                        
                        if price > max_price and price > 0:
                            continue
                        
                        prop = Property(
                            id=prop_id,
                            title=title,
                            address=address,
                            price=price if price > 0 else None,
                            url=url,
                            description=text[:500],
                            tenure="Unknown",
                            agent="OnTheMarket",
                            price_display=price_display
                        )
                        properties.append(prop)
                        
                    except Exception:
                        continue
                
                print(f"   Found {len(properties)} properties on OnTheMarket.")
                return properties

            except Exception as e:
                print(f"[!] OnTheMarket Scraper Error: {e}")
                return []
            finally:
                browser.close()
