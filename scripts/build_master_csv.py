import csv
import glob
import json
import os
from typing import Dict, Iterable, List


DATA_DIR = os.path.join(os.getcwd(), "data")


def load_exa() -> Iterable[Dict]:
    for path in glob.glob(os.path.join(DATA_DIR, "exa_*.json")):
        category = os.path.basename(path)[4:-5]
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for r in data.get("results", []):
            yield {
                "source": "exa",
                "category": category,
                "name": r.get("title"),
                "brand": "",
                "url": r.get("url"),
                "postcode": "",
                "lat": "",
                "lon": "",
                "phone": "",
                "rating": "",
                "price_level": "",
                "business_status": "",
                "opening_hours": "",
            }


def load_osm() -> Iterable[Dict]:
    for path in glob.glob(os.path.join(DATA_DIR, "osm_*.json")):
        category = os.path.basename(path)[4:-5]
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for el in data.get("elements", []):
            yield {
                "source": "osm",
                "category": category,
                "name": el.get("name"),
                "brand": el.get("brand") or "",
                "url": el.get("website") or "",
                "postcode": el.get("postcode") or "",
                "lat": el.get("lat") or "",
                "lon": el.get("lon") or "",
                "phone": "",
                "rating": "",
                "price_level": "",
                "business_status": "",
                "opening_hours": "",
            }


def load_places() -> Iterable[Dict]:
    for path in glob.glob(os.path.join(DATA_DIR, "places_*.json")):
        category = os.path.basename(path)[7:-5]  # Remove "places_" prefix and ".json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for place in data.get("places", []):
            opening_hours = place.get("opening_hours", [])
            hours_str = "; ".join(opening_hours) if opening_hours else ""
            yield {
                "source": "places",
                "category": category,
                "name": place.get("name"),
                "brand": "",  # Places API doesn't typically return brand info in this format
                "url": place.get("website") or "",
                "postcode": place.get("postcode") or "",
                "lat": place.get("lat") or "",
                "lon": place.get("lon") or "",
                "phone": place.get("phone") or "",
                "rating": place.get("rating") or "",
                "price_level": place.get("price_level") or "",
                "business_status": place.get("business_status") or "",
                "opening_hours": hours_str,
            }


def main():
    rows: List[Dict] = []
    rows.extend(load_exa())
    rows.extend(load_osm())
    rows.extend(load_places())

    out_path = os.path.join(DATA_DIR, "london_lbe_master.csv")
    fieldnames = [
        "source",
        "category", 
        "name",
        "brand",
        "url",
        "postcode",
        "lat",
        "lon",
        "phone",
        "rating",
        "price_level", 
        "business_status",
        "opening_hours",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    # Print summary by source and category
    from collections import defaultdict
    source_counts = defaultdict(int)
    category_counts = defaultdict(int)
    source_category_counts = defaultdict(lambda: defaultdict(int))
    
    for row in rows:
        source_counts[row['source']] += 1
        category_counts[row['category']] += 1
        source_category_counts[row['source']][row['category']] += 1
    
    print(f"\nWrote {len(rows)} total rows -> {out_path}")
    print(f"\nBy source: {dict(source_counts)}")
    print(f"By category: {dict(category_counts)}")
    print(f"\nDetailed breakdown:")
    for source in sorted(source_category_counts.keys()):
        print(f"  {source}:")
        for category in sorted(source_category_counts[source].keys()):
            count = source_category_counts[source][category]
            print(f"    {category}: {count}")
    print()


if __name__ == "__main__":
    main()

