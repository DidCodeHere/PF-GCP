#!/usr/bin/env python3
"""
Scrape for Web - GitHub Actions Script

This script is designed to run in GitHub Actions to refresh property data.
It includes robust timeout protection and error handling to prevent infinite runs.

Usage:
    python scripts/scrape_for_web.py --locations "Liverpool,Manchester" --max-price 100000
"""

import argparse
import json
import os
import sys
import signal
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.scraper import Scraper
from src.analyzer import PropertyAnalyzer
from src.models import Property


# Global timeout for entire script (25 minutes for nationwide)
SCRIPT_TIMEOUT = 25 * 60

# Timeout per location search (3 minutes)
LOCATION_TIMEOUT = 3 * 60

# Timeout per source (60 seconds)
SOURCE_TIMEOUT = 60

# Major English cities for comprehensive nationwide search
# Covers all regions: North, Midlands, South, East, West
ENGLAND_LOCATIONS = [
    # North West
    "Liverpool", "Manchester", "Preston", "Blackpool", "Bolton", "Wigan",
    # North East
    "Newcastle", "Sunderland", "Middlesbrough", "Durham",
    # Yorkshire
    "Leeds", "Sheffield", "Bradford", "Hull", "York", "Doncaster",
    # East Midlands
    "Nottingham", "Leicester", "Derby", "Lincoln",
    # West Midlands
    "Birmingham", "Coventry", "Wolverhampton", "Stoke-on-Trent",
    # East of England
    "Norwich", "Cambridge", "Ipswich", "Peterborough",
    # South East
    "Brighton", "Southampton", "Portsmouth", "Reading", "Oxford", "Milton Keynes",
    # South West
    "Bristol", "Plymouth", "Exeter", "Bournemouth", "Gloucester",
    # London (cheaper outer boroughs)
    "Croydon", "Barking", "Dagenham",
]


class TimeoutException(Exception):
    """Raised when an operation times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for script timeout."""
    raise TimeoutException("Script exceeded maximum runtime")


def search_with_timeout(scraper: Scraper, method_name: str, location: str, radius: float, max_price: int) -> List[Property]:
    """
    Execute a scraper method with a timeout.
    
    Args:
        scraper: Scraper instance
        method_name: Name of the scraper method (e.g., 'search_rightmove')
        location: Location to search
        radius: Search radius in miles
        max_price: Maximum price filter
        
    Returns:
        List of Property objects, or empty list on timeout/error
    """
    method = getattr(scraper, method_name, None)
    if not method:
        print(f"[!] Unknown method: {method_name}")
        return []
    
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(method, location, radius, max_price)
            return future.result(timeout=SOURCE_TIMEOUT)
    except FuturesTimeoutError:
        print(f"[!] TIMEOUT: {method_name} for {location} exceeded {SOURCE_TIMEOUT}s")
        return []
    except Exception as e:
        print(f"[!] ERROR: {method_name} for {location}: {e}")
        return []


def scrape_location(scraper: Scraper, analyzer: PropertyAnalyzer, location: str, max_price: int) -> List[Dict[str, Any]]:
    """
    Scrape all sources for a single location.
    
    Args:
        scraper: Scraper instance
        analyzer: PropertyAnalyzer instance
        location: Location to search
        max_price: Maximum price filter
        
    Returns:
        List of property dictionaries
    """
    print(f"\n{'='*50}")
    print(f"[*] Searching: {location}")
    print(f"{'='*50}")
    
    all_properties = []
    radius = 5.0  # Default radius
    
    # Search each source with timeout
    # Note: Nestoria API is currently down (SSL issues), disabled for now
    sources = [
        ('search_rightmove', 'Rightmove'),
        ('search_zoopla', 'Zoopla'),
        ('search_onthemarket', 'OnTheMarket'),
        ('search_auction_house', 'Auction House'),
        ('search_pugh', 'Pugh Auctions'),
        # ('search_nestoria', 'Nestoria (API)'),  # Disabled - API down
    ]
    
    for method_name, source_name in sources:
        print(f"   [{source_name}]...")
        props = search_with_timeout(scraper, method_name, location, radius, max_price)
        print(f"   [{source_name}] Found {len(props)} properties")
        all_properties.extend(props)
    
    # Deduplicate by ID
    seen_ids = set()
    unique_properties = []
    for prop in all_properties:
        if prop.id not in seen_ids:
            seen_ids.add(prop.id)
            unique_properties.append(prop)
    
    print(f"   Total unique: {len(unique_properties)}")
    
    # Analyze and score - pass entire list to analyzer
    try:
        analyzed_props = analyzer.analyze(unique_properties, exclude_land=False)
    except Exception as e:
        print(f"   [!] Error during analysis: {e}")
        analyzed_props = unique_properties  # Fall back to unanalyzed
    
    # Convert to dictionaries
    analyzed = [property_to_dict(prop, location) for prop in analyzed_props]
    
    return analyzed


def property_to_dict(prop: Property, search_location: str) -> Dict[str, Any]:
    """Convert a Property object to a dictionary."""
    return {
        "id": prop.id,
        "title": prop.title,
        "address": prop.address,
        "price": prop.price,
        "price_display": prop.price_display,
        "url": prop.url,
        "description": prop.description[:500] if prop.description else "",  # Truncate long descriptions
        "tenure": prop.tenure,
        "agent": prop.agent,
        "score": prop.investment_score,
        "category": prop.category,
        "ai_summary": prop.ai_summary,
        "llm_score": prop.llm_score,
        "llm_reasoning": prop.llm_reasoning,
        "location": search_location
    }


def main():
    parser = argparse.ArgumentParser(description='Scrape properties for web interface')
    parser.add_argument('--locations', type=str, default='england',
                        help='Comma-separated list of locations, or "england" for nationwide search')
    parser.add_argument('--max-price', type=int, default=100000,
                        help='Maximum property price')
    parser.add_argument('--output', type=str, default='data/properties.json',
                        help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Set up signal handler for script timeout (Unix only)
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(SCRIPT_TIMEOUT)
    
    # Handle special "england" keyword for nationwide search
    if args.locations.lower().strip() == 'england':
        locations = ENGLAND_LOCATIONS
        location_display = f"All England ({len(locations)} cities)"
    else:
        locations = [loc.strip() for loc in args.locations.split(',')]
        location_display = args.locations
    
    print(f"Smart Property Finder - Web Scraper")
    print(f"===================================")
    print(f"Locations: {location_display}")
    print(f"Max Price: £{args.max_price:,}")
    print(f"Output: {args.output}")
    print(f"Script Timeout: {SCRIPT_TIMEOUT}s")
    print()
    
    scraper = Scraper()
    analyzer = PropertyAnalyzer()
    
    all_properties = []
    
    for location in locations:
        try:
            props = scrape_location(scraper, analyzer, location, args.max_price)
            all_properties.extend(props)
        except TimeoutException:
            print(f"[!] Timeout while searching {location}, moving on...")
            continue
        except Exception as e:
            print(f"[!] Error searching {location}: {e}")
            continue
    
    # Deduplicate again (cross-location)
    seen_ids = set()
    unique_properties = []
    for prop in all_properties:
        if prop['id'] not in seen_ids:
            seen_ids.add(prop['id'])
            unique_properties.append(prop)
    
    # Sort by score descending
    unique_properties.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Build output data
    output_data = {
        "lastUpdated": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "locations": locations,
        "maxPrice": args.max_price,
        "totalCount": len(unique_properties),
        "properties": unique_properties
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"[✓] Complete! Exported {len(unique_properties)} properties")
    print(f"[✓] Output: {args.output}")
    print(f"{'='*50}")
    
    # Cancel alarm if set
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except TimeoutException as e:
        print(f"\n[!] FATAL: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] FATAL ERROR: {e}")
        sys.exit(1)
