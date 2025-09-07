#!/usr/bin/env python3
"""
Export entertainment venue data from Google Places API (New) for London.

Uses OAuth2 authentication with gcloud credentials.
Outputs JSON files for each category with comprehensive venue details.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Any, Optional


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def get_access_token() -> str:
    """Get OAuth2 access token from gcloud."""
    import subprocess
    try:
        result = subprocess.run(['gcloud', 'auth', 'print-access-token'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"Failed to get access token: {e}")


def http_post(url: str, body: Dict[str, Any], headers: Dict[str, str], timeout: int = 30) -> Dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def search_places(category: str, query: str, project_id: str = "lasertag-461314") -> Dict[str, Any]:
    """Search for places using Google Places API (New)."""
    endpoint = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_access_token()}",
        "X-Goog-User-Project": project_id,
        "X-Goog-FieldMask": ",".join([
            "places.displayName",
            "places.formattedAddress", 
            "places.location",
            "places.types",
            "places.websiteUri",
            "places.nationalPhoneNumber",
            "places.internationalPhoneNumber",
            "places.businessStatus",
            "places.priceLevel",
            "places.rating",
            "places.userRatingCount",
            "places.regularOpeningHours",
            "places.id",
            "places.googleMapsUri",
            "places.plusCode",
        ]),
    }
    
    body = {
        "textQuery": query,
        "regionCode": "GB",
        "languageCode": "en",
        "pageSize": 20,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": 51.5074,
                    "longitude": -0.1278
                },
                "radius": 50000  # 50km radius from central London
            }
        }
    }
    
    try:
        response = http_post(endpoint, body, headers)
        time.sleep(0.1)  # Rate limiting
        return response
    except Exception as e:
        print(f"Error searching for {category}: {e}")
        return {"places": []}


def extract_postcode(address: str) -> Optional[str]:
    """Extract UK postcode from address."""
    import re
    postcode_pattern = r'([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})'
    match = re.search(postcode_pattern, address.upper())
    return match.group(1).replace(' ', ' ') if match else None


def normalize_place(place: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize place data from Google Places API."""
    location = place.get("location", {})
    display_name = place.get("displayName", {})
    opening_hours = place.get("regularOpeningHours", {})
    
    address = place.get("formattedAddress", "")
    postcode = extract_postcode(address) if address else None
    
    return {
        "name": display_name.get("text") if display_name else None,
        "address": address,
        "postcode": postcode,
        "lat": location.get("latitude"),
        "lon": location.get("longitude"),
        "website": place.get("websiteUri"),
        "phone": place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber"),
        "business_status": place.get("businessStatus"),
        "price_level": place.get("priceLevel"),
        "rating": place.get("rating"),
        "user_rating_count": place.get("userRatingCount"),
        "types": place.get("types", []),
        "google_maps_uri": place.get("googleMapsUri"),
        "place_id": place.get("id"),
        "plus_code": place.get("plusCode", {}).get("globalCode"),
        "opening_hours": opening_hours.get("weekdayDescriptions", []) if opening_hours else [],
    }


# Entertainment categories for London
CATEGORIES = [
    ("bowling", "bowling London"),
    ("karting", "go karting London"), 
    ("mini_golf", "mini golf London"),
    ("trampoline", "trampoline park London"),
    ("laser_tag", "laser tag London"),
    ("vr_arcade", "VR arcade London"),
    ("escape_rooms", "escape rooms London"),
    ("paintball", "paintball London"),
    ("axe_throwing", "axe throwing London"),
    ("climbing", "climbing wall London"),
    ("ice_skating", "ice skating London"),
    ("soft_play", "soft play London"),
    ("arcade_bar", "arcade bar London"),
    ("indoor_skydiving", "indoor skydiving London"),
    ("roller_skating", "roller skating London"),
]


def main() -> None:
    out_dir = os.path.join(os.getcwd(), "data")
    ensure_dir(out_dir)
    
    summary = {}
    
    for category, query in CATEGORIES:
        print(f"Searching Google Places for: {category}...")
        
        response = search_places(category, query)
        places = response.get("places", [])
        
        # Normalize place data
        normalized_places = [normalize_place(place) for place in places]
        
        # Save category data
        output_data = {
            "category": category,
            "query": query,
            "count": len(normalized_places),
            "places": normalized_places
        }
        
        output_path = os.path.join(out_dir, f"places_{category}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        summary[category] = len(normalized_places)
        print(f"  Found {len(normalized_places)} places")
    
    # Save summary
    with open(os.path.join(out_dir, "places_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nTotal venues found: {sum(summary.values())}")
    print("Done. Files saved to data/ directory.")


if __name__ == "__main__":
    main()