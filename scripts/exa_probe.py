import os
from typing import Dict, List

from dotenv import load_dotenv
from exa_py import Exa


def run_query(exa: Exa, label: str, query: str, include_domains: List[str], n: int = 8) -> List[Dict]:
    res = exa.search(query, num_results=n, include_domains=include_domains)
    rows = []
    for r in res.results:
        rows.append({
            "title": r.title or "(no title)",
            "url": r.url,
        })
    print(f"\n=== {label} ===\nQuery: {query}\n")
    for i, row in enumerate(rows, 1):
        print(f"{i:2d}. {row['title']}\n    {row['url']}")
    return rows


def main():
    load_dotenv()
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise SystemExit("Missing EXA_API_KEY. Add it to .env")
    exa = Exa(api_key)

    queries = [
        ("Bowling", "bowling London", [
            "hollywoodbowl.co.uk", "tenpin.co.uk", "allstarlanes.co.uk", "queens.london", "rowans.co.uk",
            "timeout.com", "designmynight.com"
        ]),
        ("Karting", "go karting London", [
            "team-sport.co.uk", "capitalkarts.com", "revolutionkarting.com", "teamworks-karting.com",
            "timeout.com", "designmynight.com"
        ]),
        ("Mini Golf", "mini golf London", [
            "puttshack.com", "swingersldn.com", "junkyardgolfclub.co.uk", "playbirdies.com",
            "timeout.com", "designmynight.com"
        ]),
        ("Trampoline", "trampoline park London", [
            "oxygenfreejumping.co.uk", "flipout.co.uk", "gravity-global.com", "jumpin.com",
            "timeout.com"
        ]),
        ("Laser Tag", "laser tag London", [
            "laserquest.co.uk", "bunker51.co.uk", "lasermayhem.co.uk", "namcofunscape.com",
            "timeout.com"
        ]),
        ("VR & Arcades", "VR arcade London", [
            "sandboxvr.com", "other.world", "dnavr.co.uk", "meetspacevr.co.uk",
            "nq64.co.uk", "gravity-global.com", "fairgame.co.uk", "timeout.com"
        ]),
        ("Escape Rooms", "escape rooms London", [
            "cluequest.co.uk", "aimescape.com", "escapehunt.com", "missionbreakout.london",
            "breakinescaperooms.co.uk", "enigmaquests.london", "timeout.com"
        ]),
    ]

    for label, query, domains in queries:
        run_query(exa, label, query, domains, n=10)


if __name__ == "__main__":
    main()

