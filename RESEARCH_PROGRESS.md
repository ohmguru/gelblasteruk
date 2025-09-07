## London LBE Research — Progress Summary

### Scope
- Goal: Build a structured dataset of location-based entertainment (LBE) venues in the UK, starting with London.
- Categories covered: bowling, karting, mini golf, trampoline parks, laser tag, VR/arcades, escape rooms, amusement arcades.

### Data Collected (exported to `data/`)
- Exa (operator/aggregator search, 10 results per category):
  - Files: `exa_*.json` with fields: title, url, id, publishedDate, author.
  - Summary: `exa_summary.json`.
- OSM (Overpass for Greater London):
  - Files: `osm_*.json` with normalized fields: name, brand, website, postcode, lat, lon, raw_tags.
  - Summary: `osm_summary.json`.
- Combined seed:
  - `london_lbe_master.csv` (199 rows) with columns: source, category, name, brand, url, postcode, lat, lon.

### Quick Findings (counts)
- OSM probe suggests broad coverage: bowling (~17), karting (~26), mini golf (~33), trampoline (~5), escape rooms (~13), amusement arcades (~34). Laser tag underrepresented due to tagging.
- Exa emphasizes official operator pages and curated lists; good for authoritative locations and booking links.

### Next Actions
- Expand Exa pulls (increase num_results, relax domain filters to capture independents).
- Add Exa `search_and_contents` for operator “locations” pages; parse addresses/postcodes.
- Enrich OSM with borough and category normalization; de-duplicate by name+postcode or geohash.
- Add VR venues to OSM side by name search (Sandbox VR, OTHERWORLD, DNA VR) if not tagged.
- Produce a validated London list, then extend to UK regions.

### Repro/Usage
- Env: `.env` with `EXA_API_KEY`.
- Scripts:
  - `python3 scripts/exa_export.py`
  - `python3 scripts/osm_export.py`
  - `python3 scripts/build_master_csv.py`
- Outputs appear in `data/` as listed above.

