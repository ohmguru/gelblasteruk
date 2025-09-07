import json
import os
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from exa_py import Exa


CATEGORIES: List[Tuple[str, str, List[str]]] = [
    (
        "bowling",
        "bowling London",
        [
            "hollywoodbowl.co.uk",
            "tenpin.co.uk",
            "allstarlanes.co.uk",
            "queens.london",
            "rowans.co.uk",
            "timeout.com",
            "designmynight.com",
        ],
    ),
    (
        "karting",
        "go karting London",
        [
            "team-sport.co.uk",
            "capitalkarts.com",
            "revolutionkarting.com",
            "teamworks-karting.com",
            "timeout.com",
            "designmynight.com",
        ],
    ),
    (
        "mini_golf",
        "mini golf London",
        [
            "puttshack.com",
            "swingersldn.com",
            "junkyardgolfclub.co.uk",
            "playbirdies.com",
            "timeout.com",
            "designmynight.com",
        ],
    ),
    (
        "trampoline",
        "trampoline park London",
        [
            "oxygenfreejumping.co.uk",
            "flipout.co.uk",
            "gravity-global.com",
            "timeout.com",
        ],
    ),
    (
        "laser_tag",
        "laser tag London",
        [
            "laserquest.co.uk",
            "bunker51.co.uk",
            "lasermayhem.co.uk",
            "timeout.com",
            "designmynight.com",
        ],
    ),
    (
        "vr_arcade",
        "VR arcade London",
        [
            "sandboxvr.com",
            "other.world",
            "dnavr.co.uk",
            "meetspacevr.co.uk",
            "nq64.co.uk",
            "gravity-global.com",
            "fairgame.co.uk",
            "timeout.com",
        ],
    ),
    (
        "escape_rooms",
        "escape rooms London",
        [
            "cluequest.co.uk",
            "aimescape.com",
            "escapehunt.com",
            "missionbreakout.london",
            "breakinescaperooms.co.uk",
            "enigmaquests.london",
            "timeout.com",
        ],
    ),
    (
        "paintball",
        "paintball London",
        [
            "deltaforcepaintball.com",
            "paintballgames.co.uk",
            "battlefieldlive.co.uk",
            "commandpaintball.com",
            "timeout.com",
            "designmynight.com",
        ],
    ),
    (
        "axe_throwing",
        "axe throwing London",
        [
            "whistle-punks.com",
            "badaxethrowing.co.uk",
            "timberdodge.com",
            "hatchet-harry.co.uk",
            "timeout.com",
            "designmynight.com",
        ],
    ),
    (
        "climbing",
        "climbing wall London",
        [
            "castle-climbing.co.uk",
            "theclimbingcentre.co.uk",
            "strongholdclimbing.com",
            "climbing-wall.co.uk",
            "biscuitfactory.org.uk",
            "timeout.com",
        ],
    ),
    (
        "ice_skating",
        "ice skating London",
        [
            "broadgateice.co.uk",
            "queenoficeskating.com",
            "alexandrapalace.com",
            "somerset-house.org.uk",
            "timeout.com",
            "designmynight.com",
        ],
    ),
    (
        "soft_play",
        "soft play London",
        [
            "gambadoplay.com",
            "partyman.world",
            "kidspace.co.uk",
            "play.com",
            "timeout.com",
        ],
    ),
    (
        "arcade_bar",
        "arcade bar London",
        [
            "four-quarters.com",
            "ladbiblebar.co.uk",
            "nq64.co.uk",
            "pixelbar.co.uk",
            "drinkshop-do.com",
            "timeout.com",
            "designmynight.com",
        ],
    ),
    (
        "indoor_skydiving",
        "indoor skydiving London",
        [
            "iflysurrey.com",
            "ifly.com",
            "bodyflight.co.uk",
            "skydive-london.co.uk",
            "timeout.com",
        ],
    ),
    (
        "roller_skating",
        "roller skating London",
        [
            "rollerscape.co.uk",
            "rollerdisco.com",
            "rollerstop.co.uk",
            "timeout.com",
            "designmynight.com",
        ],
    ),
]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def export_category(exa: Exa, out_dir: str, key: str, query: str, domains: List[str]) -> Dict:
    res = exa.search(query, num_results=10, include_domains=domains)
    data = {
        "category": key,
        "query": query,
        "results": [
            {
                "title": r.title,
                "url": r.url,
                "id": r.id,
                "publishedDate": getattr(r, "publishedDate", None),
                "author": getattr(r, "author", None),
            }
            for r in res.results
        ],
    }
    out_path = os.path.join(out_dir, f"exa_{key}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def main() -> None:
    load_dotenv()
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise SystemExit("Missing EXA_API_KEY in environment or .env")
    exa = Exa(api_key)

    out_dir = os.path.join(os.getcwd(), "data")
    ensure_dir(out_dir)

    summary = {}
    for key, query, domains in CATEGORIES:
        print(f"Exporting Exa category: {key} ...")
        data = export_category(exa, out_dir, key, query, domains)
        summary[key] = len(data["results"])
    with open(os.path.join(out_dir, "exa_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Done.")


if __name__ == "__main__":
    main()

