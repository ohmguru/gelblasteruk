#!/usr/bin/env python3
"""
Compare discovery/extraction across Exa, Google Places, and Gemini.

Outputs:
- reports/tool_compare.json: raw metrics and sample records
- reports/tool_compare.md: concise comparison with usage & estimated cost

This script is designed to run small probes so you can evaluate coverage, quality,
and rough cost. It avoids SDKs and uses HTTP directly. Keys come from .env.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

# Optional: Service account OAuth for Google APIs
try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GARequest
    import requests
except Exception:
    service_account = None
    GARequest = None
    requests = None

try:
    from dotenv import load_dotenv
except Exception:  # optional
    def load_dotenv():
        return None


UK_POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})\b", re.I)


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


@dataclass
class ExaMetrics:
    requests: int = 0
    pages_retrieved: int = 0
    cost_dollars_reported: float = 0.0
    results: List[Dict[str, Any]] = None  # type: ignore


@dataclass
class PlacesMetrics:
    requests: int = 0
    results_count: int = 0
    results: List[Dict[str, Any]] = None  # type: ignore
    notes: List[str] = None  # type: ignore


@dataclass
class GeminiMetrics:
    requests: int = 0
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    total_tokens: int = 0
    parsed_records: List[Dict[str, Any]] = None  # type: ignore


def http_post(url: str, body: Dict[str, Any], headers: Dict[str, str], timeout: int = 30) -> Dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def load_service_account_token(scopes: List[str], sa_path: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Create an OAuth2 access token from a Google service account file.
    Returns the access token string or None if unavailable.
    """
    if service_account is None or GARequest is None:
        return None, None
    if not sa_path:
        # default filenames to search
        candidates = [
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            "lasertag-461314-a4ce087daaa4.json",
            "lasertag-461314-5b0e24a2cf34.json",
        ]
        candidates = [p for p in candidates if p]
    else:
        candidates = [sa_path]
    for path in candidates:
        if path and os.path.exists(path):
            try:
                creds = service_account.Credentials.from_service_account_file(path, scopes=scopes)
                creds.refresh(GARequest())
                # read project_id to set X-Goog-User-Project for Places API (New)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        sa_data = json.load(f)
                    project_id = sa_data.get("project_id")
                except Exception:
                    project_id = None
                return creds.token, project_id
            except Exception:
                continue
    return None, None


def fetch_project_number(project_id: str, sa_path: Optional[str] = None) -> Optional[str]:
    """Attempt to resolve a GCP project number from project_id using Cloud Resource Manager.
    Requires service account to have resourcemanager.projects.get and an OAuth token with cloud-platform scope.
    """
    if requests is None:
        return None
    token, _ = load_service_account_token(["https://www.googleapis.com/auth/cloud-platform"], sa_path)
    if not token:
        return None
    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}"
    try:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            num = data.get("projectNumber")
            return str(num) if num else None
        else:
            return None
    except Exception:
        return None


def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def exa_get_contents(api_key: str, urls: List[str], *, text: bool = True, livecrawl: str = "preferred",
                     subpages: int = 0, subpage_target: Optional[List[str]] = None, extras: Optional[Dict[str, Any]] = None,
                     timeout_ms: int = 10000) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "urls": urls,
    }
    if text:
        body["text"] = True
    if livecrawl:
        body["livecrawl"] = livecrawl
    if subpages:
        body["subpages"] = subpages
    if subpage_target:
        body["subpageTarget"] = subpage_target
    if extras:
        body["extras"] = extras
    body["livecrawlTimeout"] = timeout_ms
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "accept": "application/json",
    }
    return http_post("https://api.exa.ai/contents", body, headers)


def extract_postcodes(text: str) -> List[str]:
    pcs = set()
    for m in UK_POSTCODE_RE.finditer(text or ""):
        pcs.add((m.group(1) + m.group(2)).upper())
    return sorted(pcs)


def probe_exa(api_key: str) -> ExaMetrics:
    metrics = ExaMetrics(requests=0, pages_retrieved=0, cost_dollars_reported=0.0, results=[])
    # Small operator seed to keep cost low; adjust as needed
    seeds = [
        "https://sandboxvr.com/",
        "https://www.other.world/",
        "https://www.dnavr.co.uk/",
        "https://www.hollywoodbowl.co.uk/",
        "https://www.tenpin.co.uk/",
        "https://www.flipout.co.uk/",
    ]
    for url in seeds:
        resp = exa_get_contents(
            api_key,
            urls=[url],
            text=True,
            livecrawl="preferred",
            subpages=3,
            subpage_target=["locations", "venues", "find-us", "london"],
            extras={"links": 5},
            timeout_ms=10000,
        )
        metrics.requests += 1
        metrics.cost_dollars_reported += float(resp.get("costDollars", {}).get("total", 0.0))
        for r in resp.get("results", []) or []:
            metrics.pages_retrieved += 1
            text = r.get("text") or ""
            metrics.results.append({
                "url": r.get("url"),
                "title": r.get("title"),
                "postcodes": extract_postcodes(text),
            })
        time.sleep(0.2)  # small backoff
    return metrics


def probe_places_textsearch_legacy(google_api_key: str) -> PlacesMetrics:
    metrics = PlacesMetrics(requests=0, results_count=0, results=[])
    queries = [
        "laser tag in London",
        "vr arcade in London",
        "trampoline park in London",
    ]
    for q in queries:
        params = urllib.parse.urlencode({
            "query": q,
            "key": google_api_key,
            "region": "gb",
        })
        url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?{params}"
        try:
            data = http_get(url)
        except Exception:
            data = {"results": []}
        metrics.requests += 1
        results = data.get("results", [])
        metrics.results_count += len(results)
        for r in results:
            metrics.results.append({
                "name": r.get("name"),
                "formatted_address": r.get("formatted_address"),
                "types": r.get("types"),
                "location": (r.get("geometry", {}).get("location") or {}),
                "place_id": r.get("place_id"),
            })
        time.sleep(0.2)
    return metrics


def probe_places_textsearch_new(google_api_key: str) -> PlacesMetrics:
    """Use Places API (New) searchText endpoint."""
    metrics = PlacesMetrics(requests=0, results_count=0, results=[], notes=[])
    endpoint = "https://places.googleapis.com/v1/places:searchText"
    queries = [
        "laser tag in London",
        "vr arcade in London",
        "trampoline park in London",
    ]
    def is_bearer(token: str) -> bool:
        return token.startswith(("ya29.", "AQ.")) or token.count(".") >= 2

    headers = {
        "Content-Type": "application/json",
        # Field mask is required by Places API (New)
        "X-Goog-FieldMask": ",".join(
            [
                "places.displayName",
                "places.formattedAddress",
                "places.types",
                "places.location",
                "places.id",
                "places.websiteUri",
            ]
        ),
    }
    bearer = None
    project_id = None
    if is_bearer(google_api_key):
        bearer = google_api_key
    if not bearer:
        # Try service account OAuth for Places API (New)
        bearer, project_id = load_service_account_token(["https://www.googleapis.com/auth/maps-platform.places"]) or (None, None)
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
        # Set billing project for OAuth requests
        # Prefer explicit project number if provided
        proj_number = os.getenv("GOOGLE_PROJECT_NUMBER")
        if proj_number:
            headers["X-Goog-User-Project"] = proj_number
        elif project_id:
            # As a fallback, try project_id if number not provided
            # Attempt to resolve numeric project number via Cloud Resource Manager
            proj_num = fetch_project_number(project_id)
            if proj_num:
                headers["X-Goog-User-Project"] = proj_num
            else:
                headers["X-Goog-User-Project"] = project_id
    else:
        headers["X-Goog-Api-Key"] = google_api_key
    for q in queries:
        body = {
            "textQuery": q,
            "regionCode": "GB",
            "languageCode": "en",
            "pageSize": 20,
        }
        try:
            data = http_post(endpoint, body, headers=headers)
        except Exception as e:
            metrics.notes.append(f"searchText error: {type(e).__name__}: {e}")
            data = {"places": []}
        metrics.requests += 1
        results = data.get("places", [])
        if not results and data.get("error"):
            # capture API error message if present
            try:
                err = data["error"].get("message") or str(data["error"])  # type: ignore
                metrics.notes.append(f"API error: {err}")
            except Exception:
                pass
        metrics.results_count += len(results)
        for r in results:
            loc = r.get("location") or {}
            metrics.results.append({
                "name": r.get("displayName", {}).get("text") or r.get("name"),
                "formatted_address": r.get("formattedAddress"),
                "types": r.get("types"),
                "location": {"lat": loc.get("latitude"), "lng": loc.get("longitude")},
                "place_id": r.get("id") or r.get("placeId"),
                "website": (r.get("websiteUri") or r.get("websiteUri", "")),
            })
        time.sleep(0.2)
    return metrics


def probe_gemini_extract(google_api_key: str, pages: List[Dict[str, Any]]) -> GeminiMetrics:
    """Run structured extraction for a few pages. Uses v1beta generateContent."""
    metrics = GeminiMetrics(requests=0, prompt_tokens=0, candidates_tokens=0, total_tokens=0, parsed_records=[])
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    def is_bearer(token: str) -> bool:
        return token.startswith(("ya29.", "AQ.")) or token.count(".") >= 2

    base = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    bearer = None
    if is_bearer(google_api_key):
        bearer = google_api_key
    if not bearer:
        # Try service account OAuth for Generative Language
        bearer, _ = load_service_account_token(["https://www.googleapis.com/auth/generative-language"]) or (None, None)
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
        endpoint = base
    else:
        endpoint = f"{base}?key={google_api_key}"

    schema_instructions = (
        "Extract venue records as JSON array with objects: "
        "{name, brand, website, phone, address, postcode}. "
        "Only output JSON, no prose."
    )

    # take up to 3 pages to control cost
    for page in pages[:3]:
        text = page.get("text") or page.get("content") or page.get("page_text") or ""
        url = page.get("url") or ""
        if not text:
            continue
        body = {
            "tools": [{"googleSearchRetrieval": {}}],  # enable grounded search tool
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": schema_instructions + f"\nSource URL: {url}\n\n" + text[:15000]}
                    ],
                }
            ],
        }
        try:
            resp = http_post(endpoint, body, headers=headers)
        except Exception as e:
            # Unauthorized or API not enabled; skip Gemini and continue
            # We still return whatever metrics we have so far
            # Mark a synthetic note record to signal failure reason
            metrics.parsed_records.append({
                "_error": f"gemini_request_failed: {type(e).__name__}"
            })
            continue
        metrics.requests += 1
        # usage
        usage = resp.get("usageMetadata") or {}
        metrics.prompt_tokens += int(usage.get("promptTokenCount", 0))
        metrics.candidates_tokens += int(usage.get("candidatesTokenCount", 0))
        metrics.total_tokens += int(usage.get("totalTokenCount", 0))
        # parse JSON candidate
        try:
            text_json = resp.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            parsed = json.loads(text_json) if text_json else []
            if isinstance(parsed, dict):
                parsed = [parsed]
            for obj in parsed:
                # normalize postcode if not provided
                if not obj.get("postcode") and obj.get("address"):
                    pcs = extract_postcodes(obj.get("address", ""))
                    if pcs:
                        obj["postcode"] = pcs[0]
                metrics.parsed_records.append(obj)
        except Exception:
            pass
        time.sleep(0.2)
    return metrics


def main() -> None:
    load_dotenv()
    # Load keys from .env; if missing, try keys.local.txt
    exa_key = os.getenv("EXA_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    if not (exa_key and google_key) and os.path.exists("keys.local.txt"):
        with open("keys.local.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k and v:
                    os.environ.setdefault(k, v)
        exa_key = os.getenv("EXA_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
    if not exa_key or not google_key:
        raise SystemExit("Missing EXA_API_KEY or GOOGLE_API_KEY in environment")

    ensure_dir("reports")

    # 1) Exa probe: crawl seed operator domains and capture pages + costs
    exa_metrics = probe_exa(exa_key)

    # For Gemini, we need page text. Get a small subset of pages via Exa again but requesting text explicitly
    sample_pages: List[Dict[str, Any]] = []
    # re-fetch content for the first 2 seed URLs to ensure text payload presence for Gemini
    refetch_urls = [r["url"] for r in exa_metrics.results[:2] if r.get("url")]
    if refetch_urls:
        exa_resp = exa_get_contents(exa_key, urls=refetch_urls, text=True, livecrawl="preferred")
        for r in exa_resp.get("results", []) or []:
            sample_pages.append({"url": r.get("url"), "text": r.get("text", "")})

    # 2) Places probe: try Places API (New) first, then fall back to legacy
    places_metrics = probe_places_textsearch_new(google_key)
    if places_metrics.results_count == 0:
        fallback = probe_places_textsearch_legacy(google_key)
        # prefer whichever returned results; if both 0, keep new for consistency
        if fallback.results_count > 0:
            places_metrics = fallback

    # 3) Gemini extraction: structured output on a few sample pages
    gemini_metrics = probe_gemini_extract(google_key, sample_pages)

    # Aggregate & simple cost estimates
    unit_price_exa_contents = env_float("UNIT_PRICE_EXA_CONTENTS_PER_PAGE", 0.001)
    unit_price_gemini_per_1k_tokens = env_float("UNIT_PRICE_GEMINI_USD_PER_1K_TOKENS", 0.0)
    unit_price_places_textsearch_per_1000 = env_float("UNIT_PRICE_PLACES_TEXTSEARCH_PER_1000", 0.0)

    est_exa_cost = exa_metrics.cost_dollars_reported
    if not est_exa_cost:
        est_exa_cost = unit_price_exa_contents * max(exa_metrics.pages_retrieved, 0)

    est_gemini_cost = (gemini_metrics.total_tokens / 1000.0) * unit_price_gemini_per_1k_tokens
    est_places_cost = (places_metrics.requests / 1000.0) * unit_price_places_textsearch_per_1000

    report: Dict[str, Any] = {
        "timestamp": int(time.time()),
        "exa": {
            **asdict(exa_metrics),
            "estimated_cost_usd": round(est_exa_cost, 6),
        },
        "places": {
            **asdict(places_metrics),
            "estimated_cost_usd": round(est_places_cost, 6),
        },
        "gemini": {
            **asdict(gemini_metrics),
            "estimated_cost_usd": round(est_gemini_cost, 6),
        },
    }

    with open("reports/tool_compare.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Simple human-readable summary
    lines: List[str] = []
    lines.append("# Tool Comparison — Probe Summary\n")
    lines.append("## Exa (contents + subpages)\n")
    lines.append(f"Requests: {exa_metrics.requests}, pages: {exa_metrics.pages_retrieved}, cost_reported: ${exa_metrics.cost_dollars_reported:.4f}, est_cost: ${est_exa_cost:.4f}")
    lines.append(f"Sample extracted postcodes count: {sum(len(r.get('postcodes', [])) for r in exa_metrics.results)}\n")
    lines.append("## Google Places (Text Search)\n")
    lines.append(f"Requests: {places_metrics.requests}, results: {places_metrics.results_count}, est_cost: ${est_places_cost:.4f}\n")
    lines.append("## Gemini (structured extraction)\n")
    lines.append(f"Requests: {gemini_metrics.requests}, tokens: {gemini_metrics.total_tokens} (prompt {gemini_metrics.prompt_tokens} / candidates {gemini_metrics.candidates_tokens}), est_cost: ${est_gemini_cost:.4f}\n")
    lines.append("## Notes\n")
    lines.append("- Costs for Places and Gemini are estimates; set UNIT_PRICE_* in .env for accurate numbers.")
    lines.append("- Exa cost may be returned per response; if missing, estimate uses per-page unit price.")

    with open("reports/tool_compare.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print("Wrote reports/tool_compare.json and reports/tool_compare.md")


if __name__ == "__main__":
    main()
