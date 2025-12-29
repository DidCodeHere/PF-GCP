from src.scraper import Scraper

def test_zoopla():
    s = Scraper()
    results = s.search_zoopla("Liverpool", 1.0, 100000)
    print(f"Found {len(results)} results.")
    for p in results[:3]:
        print(f"- {p.title} @ {p.address} (£{p.price})")
        print(f"  URL: {p.url}")

if __name__ == "__main__":
    test_zoopla()
