#!/usr/bin/env python3
"""Enrich existing properties.json with listing images.

Best-effort strategy:
- Fetch each property URL (throttled)
- Extract a representative image URL from:
  - <meta property="og:image" ...>
  - <meta name="twitter:image" ...>
  - JSON-LD "image" fields

Writes back into data/properties.json (or a provided path) adding:
- image_url

A small persistent cache is stored in data/image_cache.json.

Usage:
  python scripts/enrich_images.py
  python scripts/enrich_images.py --data data/properties.json --max-images 500
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup


CACHE_PATH = Path("data/image_cache.json")


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _norm_url(url: str) -> str:
    url = (url or "").strip()
    if url.startswith("//"):
        return "https:" + url
    return url


def _iter_jsonld_images(soup: BeautifulSoup) -> Iterable[str]:
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string
        if not raw:
            continue
        raw = raw.strip()
        if not raw:
            continue

        # Some pages embed multiple JSON-LD objects or invalid JSON.
        # We'll try a couple of tolerant parses.
        candidates: List[Any] = []
        try:
            candidates.append(json.loads(raw))
        except Exception:
            # Try to extract the first JSON object/array substring.
            m = re.search(r"(\{.*\}|\[.*\])", raw, flags=re.DOTALL)
            if m:
                try:
                    candidates.append(json.loads(m.group(1)))
                except Exception:
                    pass

        for obj in candidates:
            yield from _extract_images_from_jsonld_obj(obj)


def _extract_images_from_jsonld_obj(obj: Any) -> Iterable[str]:
    if obj is None:
        return

    if isinstance(obj, list):
        for item in obj:
            yield from _extract_images_from_jsonld_obj(item)
        return

    if isinstance(obj, dict):
        # Common places
        if "image" in obj:
            img = obj["image"]
            if isinstance(img, str):
                yield img
            elif isinstance(img, list):
                for x in img:
                    if isinstance(x, str):
                        yield x
                    elif isinstance(x, dict):
                        # image objects sometimes have url
                        u = x.get("url")
                        if isinstance(u, str):
                            yield u
            elif isinstance(img, dict):
                u = img.get("url")
                if isinstance(u, str):
                    yield u

        # Walk nested objects too
        for v in obj.values():
            if isinstance(v, (dict, list)):
                yield from _extract_images_from_jsonld_obj(v)


def _score_candidate(url: str) -> int:
    """Higher is better."""
    u = (url or "").lower()

    # Prefer actual property photos
    priorities: List[Tuple[int, List[str]]] = [
        (100, ["property-photo", "dir/crop", "rm" ]),
        (90, ["lid.zoocdn", "zoocdn", "media.zoopla", "zoopla" ]),
        (80, ["uploads", "images", "cdn"]),
    ]

    score = 0
    for pts, needles in priorities:
        if any(n in u for n in needles):
            score = max(score, pts)

    # De-prioritize obvious logos/icons
    if any(x in u for x in ["logo", "favicon", "sprite", "icon", "brand"]):
        score -= 80

    # Avoid Rightmove share logo if encountered
    if "logo-share" in u:
        score -= 200

    # Prefer jpeg/webp over tiny gifs
    if u.endswith((".jpg", ".jpeg", ".webp")):
        score += 5
    if u.endswith((".gif", ".svg")):
        score -= 20

    return score


def extract_best_image_url(html: str, base_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: List[str] = []

    og = soup.find("meta", attrs={"property": "og:image"})
    if og and og.get("content"):
        candidates.append(og["content"])

    tw = soup.find("meta", attrs={"name": "twitter:image"})
    if tw and tw.get("content"):
        candidates.append(tw["content"])

    # JSON-LD image
    for img in _iter_jsonld_images(soup):
        candidates.append(img)

    # Normalize + filter empties
    normed: List[str] = []
    for c in candidates:
        c = _norm_url(c)
        if not c:
            continue
        normed.append(c)

    if not normed:
        return None

    # Pick best-scored
    best = max(normed, key=_score_candidate)
    if _score_candidate(best) <= 0:
        # If everything looks like junk (logos), don't set.
        return None

    return best


def enrich_images(data_path: Path, max_images: int, sleep_s: float) -> None:
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    data = _load_json(data_path)
    props: List[Dict[str, Any]] = data.get("properties", [])

    cache: Dict[str, str] = {}
    if CACHE_PATH.exists():
        try:
            cache = _load_json(CACHE_PATH)
        except Exception:
            cache = {}

    to_update = 0
    for p in props:
        if p.get("image_url"):
            continue
        url = (p.get("url") or "").strip()
        if not url:
            continue
        to_update += 1

    print(f"Loaded {len(props)} properties")
    print(f"Missing images: {to_update}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    }

    updated = 0
    attempted = 0

    with httpx.Client(headers=headers, timeout=20.0, follow_redirects=True) as client:
        for idx, p in enumerate(props, start=1):
            if updated >= max_images:
                break

            if p.get("image_url"):
                continue

            url = (p.get("url") or "").strip()
            if not url:
                continue

            # Cache hit
            if url in cache and cache[url]:
                p["image_url"] = cache[url]
                updated += 1
                continue

            attempted += 1
            if attempted % 25 == 0:
                print(f"Fetching images… attempted {attempted}, updated {updated}")

            try:
                resp = client.get(url)
                if resp.status_code >= 400:
                    continue

                img = extract_best_image_url(resp.text, url)
                if img:
                    p["image_url"] = img
                    cache[url] = img
                    updated += 1

            except Exception:
                continue
            finally:
                if sleep_s > 0:
                    time.sleep(sleep_s)

    # Persist
    data["properties"] = props
    _save_json(data_path, data)
    _save_json(CACHE_PATH, cache)

    print(f"Done. Added image_url to {updated} properties")
    print(f"Cache saved to {CACHE_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich properties.json with listing images")
    parser.add_argument("--data", type=str, default="data/properties.json", help="Path to properties.json")
    parser.add_argument("--max-images", type=int, default=500, help="Max number of properties to enrich this run")
    parser.add_argument("--sleep", type=float, default=0.15, help="Sleep between requests (seconds)")

    args = parser.parse_args()

    data_path = Path(args.data)
    enrich_images(data_path=data_path, max_images=max(0, args.max_images), sleep_s=max(0.0, args.sleep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
