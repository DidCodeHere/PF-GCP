import json
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.enricher import MarketDataEnricher

async def enrich_properties_async(data_path: str):
    if not os.path.exists(data_path):
        print(f"Error: File {data_path} not found.")
        return

    print(f"Loading data from {data_path}...")
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    properties_data = data.get('properties', [])
    
    # Load persistent cache
    cache_file = Path("data/area_stats_cache.json")
    existing_cache = {}
    if cache_file.exists():
        print(f"Loading area stats cache from {cache_file}...")
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                existing_cache = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache: {e}")

    enricher = MarketDataEnricher(cache=existing_cache)
    
    # 1. Collect all unique outcodes
    print("Identifying unique postcode areas...")
    unique_outcodes = set()
    for prop in properties_data:
        outcode = enricher.get_outcode(prop.get('address', ''))
        if outcode:
            unique_outcodes.add(outcode)
            
    print(f"Found {len(unique_outcodes)} unique areas to check.")
    
    # 2. Fetch stats for all outcodes concurrently
    print("Fetching market data (Async)...")
    await enricher.fetch_all_stats(list(unique_outcodes))
    
    # 3. Apply stats to properties
    print(f"Enriching {len(properties_data)} properties...")
    
    for i, prop_dict in enumerate(properties_data):
        address = prop_dict.get('address', '')
        outcode = enricher.get_outcode(address)
        
        if outcode:
            # Get stats (now guaranteed to be in cache if fetch succeeded)
            stats = enricher.get_cached_stats(outcode)
            
            prop_dict['avg_area_price'] = stats['avg_price']
            prop_dict['avg_area_rent'] = stats['avg_rent']
            
            # Logic 1: Calculate ROI for Standard Properties
            # ROI = (Annual Rent / Asking Price) * 100
            price = prop_dict.get('price')
            avg_rent = stats['avg_rent']
            
            if price and avg_rent and price > 0:
                annual_rent = avg_rent * 12
                roi = (annual_rent / price) * 100
                prop_dict['roi'] = round(roi, 2)
                
                # Update Score based on ROI
                # We modify the 'score' field directly. 
                # Note: This adds to the existing score from the scraper.
                current_score = prop_dict.get('score', 0)
                
                # ROI Scoring Bonus
                if roi > 15:
                    prop_dict['score'] = min(10, current_score + 3)
                elif roi > 10:
                    prop_dict['score'] = min(10, current_score + 2)
                elif roi > 7:
                    prop_dict['score'] = min(10, current_score + 1)
                elif roi < 4:
                    prop_dict['score'] = max(0, current_score - 1)

            # Logic 2: Potential Value for Auctions/Fixers
            # If asking price is significantly below area average
            avg_price = stats['avg_price']
            if price and avg_price and price > 0:
                # Calculate discount
                discount = ((avg_price - price) / avg_price) * 100
                
                if discount > 40: # 40% below market value
                    prop_dict['score'] = min(10, prop_dict.get('score', 0) + 2)
                elif discount > 20:
                    prop_dict['score'] = min(10, prop_dict.get('score', 0) + 1)

    data['properties'] = properties_data
    
    # Save persistent cache
    print(f"Saving area stats cache to {cache_file}...")
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(enricher.cache, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")

    print(f"Saving enriched data to {data_path}...")
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print("Enrichment complete!")

if __name__ == "__main__":
    # Default to the standard location
    data_file = "data/properties.json"
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        
    asyncio.run(enrich_properties_async(data_file))
