# GelBlasterUK — Data Collection & Comparison

This repository collects London LBE venue data from multiple sources (OSM, Exa, Google Places) and provides scripts to compare coverage, quality, and cost across tools. It follows the lightweight conventions in `AGENTS.md`.

## Quickstart

1) Python env
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt` (or install `python-dotenv` if not using a requirements file)

2) Environment variables
- Create a `.env` file in the project root (see `.env.example`) and set:
  - `EXA_API_KEY=...`
  - `GOOGLE_API_KEY=...` (Note: Google Places API (new) requires OAuth2, not API keys)

Important: Do NOT commit keys to the repo. Keep secrets in `.env` or your shell environment. If loading via dotenv ever fails, you can export them in the shell before running scripts:

```
export EXA_API_KEY="<your_exa_key>"
export GOOGLE_API_KEY="<your_google_key>"
```

### Google Places API (New) Authentication
The Google Places API (new) requires OAuth2 authentication instead of API keys. To make API calls:

1. Ensure you're authenticated with gcloud:
   ```bash
   gcloud auth login
   gcloud config set project your-project-id
   ```

2. Get an access token:
   ```bash
   gcloud auth print-access-token
   ```

3. Make API calls using the bearer token:
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "X-Goog-User-Project: your-project-id" \
     -H "X-Goog-FieldMask: places.displayName,places.formattedAddress,places.priceLevel" \
     -d '{
       "textQuery": "pizza restaurants in London"
     }' \
     "https://places.googleapis.com/v1/places:searchText"
   ```

Key requirements:
- Use `X-Goog-User-Project` header with your project ID for quota billing
- API endpoint: `https://places.googleapis.com/v1/places:searchText`
- Use field masks to specify which data fields you want returned

Optional for cost estimates in reports (set in `.env`):
- `UNIT_PRICE_EXA_CONTENTS_PER_PAGE=0.001`
- `UNIT_PRICE_GEMINI_USD_PER_1K_TOKENS=`
- `UNIT_PRICE_PLACES_TEXTSEARCH_PER_1000=`

3) Data scripts
- Exa categories: `python3 scripts/exa_export.py`
- OSM export: `python3 scripts/osm_export.py`
- Build CSV: `python3 scripts/build_master_csv.py`

4) Tool comparison & cost probe
- Run a small probe against Exa, Google Places, and Gemini to gather usage and estimate costs:

```
python3 scripts/compare_tools.py
```

Outputs:
- `reports/tool_compare.json` — raw metrics and sample records
- `reports/tool_compare.md` — human-readable summary

## Notes on Secrets & Licensing
- Never commit API keys or secrets. Use `.env` and `.gitignore` already excludes it.
- Google Places data has usage and redistribution restrictions; use it primarily for discovery/validation, and prefer operator websites or OSM for canonical fields.

## Repository Structure (initial)
- `scripts/` — CLI scripts for data fetch, merge, and comparison
- `data/` — exported datasets
- `reports/` — generated comparison reports (gitignored)
- `AGENTS.md` — repo conventions and guidelines

