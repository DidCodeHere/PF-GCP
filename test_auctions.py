import multiprocessing
import time
import sys
from src.scraper import Scraper

def test_auction_house_wrapper():
    print("\n--- Testing Auction House UK ---")
    s = Scraper()
    try:
        results = s.search_auction_house("Liverpool", 5.0, 100000)
        print(f"Found {len(results)} results.")
        for p in results[:3]:
            print(f"- {p.title} @ {p.address} ({p.price_display})")
    except Exception as e:
        print(f"Error in Auction House: {e}")

def test_pugh_wrapper():
    print("\n--- Testing Pugh Auctions ---")
    s = Scraper()
    try:
        results = s.search_pugh("Liverpool", 5.0, 100000)
        print(f"Found {len(results)} results.")
        for p in results[:3]:
            print(f"- {p.title} @ {p.address} ({p.price_display})")
    except Exception as e:
        print(f"Error in Pugh: {e}")

def run_with_timeout(func, timeout):
    p = multiprocessing.Process(target=func)
    p.start()
    p.join(timeout)
    
    if p.is_alive():
        print(f"\n[!] Operation timed out after {timeout} seconds. Terminating process...")
        p.terminate()
        p.join()
    else:
        print(f"\n[+] Operation finished within timeout.")

def test_auctions():
    print("Starting tests with 10s timeout per source...")
    
    # Run Auction House
    run_with_timeout(test_auction_house_wrapper, 10)
    
    # Run Pugh
    run_with_timeout(test_pugh_wrapper, 10)

if __name__ == "__main__":
    # Windows requires this for multiprocessing
    multiprocessing.freeze_support()
    test_auctions()
