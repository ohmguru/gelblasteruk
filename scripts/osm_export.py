import json
import os
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Tuple


AREA = "Greater London"

QUERIES: List[Tuple[str, str]] = [
    ("bowling", "nwr[leisure=bowling_alley](area.a);"),
    ("karting", "nwr[sport=karting](area.a); nwr[leisure=go_kart](area.a);"),
    ("trampoline", "nwr[leisure=trampoline_park](area.a);"),
    ("laser_tag", "nwr[leisure=laser_tag](area.a); nwr[sport=laser_tag](area.a); nwr[leisure=laser_game](area.a);"),
    ("mini_golf", "nwr[leisure=miniature_golf](area.a); nwr[sport=miniature_golf](area.a);"),
    ("escape_rooms", "nwr[leisure=escape_game](area.a); nwr[amenity=escape_game](area.a);"),
    ("amusement_arcade", "nwr[leisure=amusement_arcade](area.a);"),
    ("paintball", "nwr[sport=paintball](area.a); nwr[leisure=paintball](area.a);"),
    ("axe_throwing", "nwr[leisure=axe_throwing](area.a); nwr[sport=axe_throwing](area.a);"),
    ("climbing", "nwr[sport=climbing](area.a); nwr[leisure=climbing_centre](area.a);"),
    ("ice_skating", "nwr[leisure=ice_rink](area.a); nwr[sport=ice_skating](area.a);"),
    ("soft_play", "nwr[leisure=soft_play](area.a); nwr[amenity=soft_play](area.a);"),
    ("arcade_bar", "nwr[amenity=bar][arcade=yes](area.a); nwr[leisure=adult_gaming_centre](area.a);"),
    ("indoor_skydiving", "nwr[sport=skydiving][indoor=yes](area.a); nwr[leisure=indoor_skydiving](area.a);"),
    ("roller_skating", "nwr[leisure=roller_rink](area.a); nwr[sport=roller_skating](area.a);"),
    ("vr_arcade", "nwr[leisure=vr](area.a); nwr[amenity=vr_arcade](area.a); nwr[leisure=virtual_reality](area.a);"),
]


def overpass(query_body: str, timeout: int = 25, retries: int = 3) -> Dict:
    base = f"[out:json][timeout:{timeout}];area[name=\"{AREA}\"]->.a;({query_body});out center;"
    params = urllib.parse.urlencode({"data": base})
    url = f"https://overpass-api.de/api/interpreter?{params}"
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout + 5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1 + i)
    return {}


def normalize_elements(elements: List[Dict]) -> List[Dict]:
    out = []
    for el in elements:
        tags = el.get("tags", {})
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        out.append(
            {
                "type": el.get("type"),
                "id": el.get("id"),
                "name": tags.get("name"),
                "brand": tags.get("brand"),
                "website": tags.get("website"),
                "postcode": tags.get("addr:postcode"),
                "street": tags.get("addr:street"),
                "city": tags.get("addr:city"),
                "lat": lat,
                "lon": lon,
                "raw_tags": tags,
            }
        )
    return out


def main() -> None:
    out_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(out_dir, exist_ok=True)
    summary = {}
    for key, q in QUERIES:
        print(f"Exporting OSM category: {key} ...")
        data = overpass(q)
        elements = normalize_elements(data.get("elements", []))
        summary[key] = len(elements)
        with open(os.path.join(out_dir, f"osm_{key}.json"), "w", encoding="utf-8") as f:
            json.dump({"category": key, "area": AREA, "count": len(elements), "elements": elements}, f, indent=2)
    with open(os.path.join(out_dir, "osm_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Done.")


if __name__ == "__main__":
    main()

