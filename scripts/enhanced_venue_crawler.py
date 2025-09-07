#!/usr/bin/env python3
"""
Enhanced venue crawler with improved attraction parsing and diverse category sampling.
"""
import json
import os
import re
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dotenv import load_dotenv
from exa_py import Exa


def extract_diverse_venue_sample(venues: List[Dict], sample_size: int = 40) -> List[Dict]:
    """Get a diverse sample of venues across all categories."""
    venues_by_category = defaultdict(list)
    
    # Group venues by category
    for venue in venues:
        venues_by_category[venue['category']].append(venue)
    
    # Sample evenly across categories
    sample = []
    categories = list(venues_by_category.keys())
    venues_per_category = max(1, sample_size // len(categories))
    
    for category in categories:
        category_venues = venues_by_category[category][:venues_per_category]
        sample.extend(category_venues)
        if len(sample) >= sample_size:
            break
    
    return sample[:sample_size]


def enhanced_parse_attractions(content: str, category: str) -> List[str]:
    """Enhanced attraction parsing with category-specific patterns."""
    content_lower = content.lower()
    attractions = set()
    
    # Category-specific attraction patterns
    if category == "trampoline":
        patterns = [
            r'main\s+(?:bounce\s+)?court(?:s)?',
            r'foam\s+pit(?:s)?',
            r'dodgeball\s+(?:court|area)(?:s)?',
            r'basketball\s+(?:hoop|area)(?:s)?',
            r'battle\s+beam(?:s)?',
            r'ninja\s+course(?:s)?',
            r'wipeout\s+zone',
            r'slam\s+dunk(?:\s+area)?',
            r'air\s+bag(?:s)?',
            r'performance\s+trampoline(?:s)?',
            r'toddler\s+area',
        ]
    
    elif category == "bowling":
        patterns = [
            r'(?:\d+\s*)?(?:pin\s+)?bowling\s+lane(?:s)?',
            r'ten\s*pin\s*bowling',
            r'cosmic\s+bowling',
            r'glow\s+bowling',
            r'bumper\s+bowling',
            r'kids\s+bowling',
        ]
    
    elif category == "karting":
        patterns = [
            r'indoor\s+(?:go\s+)?kart(?:ing)?(?:\s+track)?',
            r'outdoor\s+(?:go\s+)?kart(?:ing)?(?:\s+track)?',
            r'electric\s+kart(?:s)?',
            r'petrol\s+kart(?:s)?',
            r'junior\s+kart(?:ing|s)?',
            r'adult\s+kart(?:ing|s)?',
            r'racing\s+simulation',
        ]
    
    elif category == "climbing":
        patterns = [
            r'bouldering\s+(?:wall|area)(?:s)?',
            r'top\s+rope\s+climbing',
            r'lead\s+climbing',
            r'auto\s+belay(?:s)?',
            r'speed\s+climbing',
            r'training\s+(?:wall|area)',
            r'competition\s+(?:wall|area)',
        ]
    
    elif category == "laser_tag":
        patterns = [
            r'laser\s+tag\s+arena(?:s)?',
            r'multi[\-\s]?level\s+arena',
            r'outdoor\s+laser(?:\s+tag)?',
            r'indoor\s+laser(?:\s+tag)?',
            r'tactical\s+laser',
            r'team\s+battles?',
        ]
    
    elif category == "escape_rooms":
        patterns = [
            r'escape\s+room(?:s)?(?:\s+theme(?:s)?)?',
            r'horror\s+escape(?:\s+room)?',
            r'mystery\s+room(?:s)?',
            r'puzzle\s+room(?:s)?',
            r'adventure\s+room(?:s)?',
            r'themed\s+room(?:s)?',
        ]
    
    elif category == "vr_arcade":
        patterns = [
            r'vr\s+(?:experience|game)(?:s)?',
            r'virtual\s+reality\s+game(?:s)?',
            r'multiplayer\s+vr',
            r'vr\s+escape(?:\s+room)?',
            r'vr\s+zombie(?:s)?',
            r'vr\s+racing',
            r'vr\s+shooting',
        ]
    
    elif category == "axe_throwing":
        patterns = [
            r'axe\s+throwing\s+lane(?:s)?',
            r'hatchet\s+throwing',
            r'tomahawk\s+throwing',
            r'knife\s+throwing',
        ]
    
    else:
        # Generic patterns for other categories
        patterns = [
            r'main\s+(?:activity|attraction)',
            r'group\s+activities',
            r'party\s+(?:room|area)(?:s)?',
        ]
    
    # Common facility patterns for all categories
    common_patterns = [
        r'birthday\s+part(?:y|ies)',
        r'group\s+booking(?:s)?',
        r'corporate\s+event(?:s)?',
        r'team\s+building',
        r'private\s+hire',
        r'party\s+package(?:s)?',
        r'food\s+(?:and\s+drink|court|area)',
        r'cafe(?:teria)?',
        r'restaurant',
        r'bar(?:\s+area)?',
        r'spectator\s+area(?:s)?',
        r'viewing\s+area(?:s)?',
        r'retail\s+(?:shop|store)',
        r'pro\s+shop',
        r'equipment\s+hire',
        r'locker(?:s)?',
        r'changing\s+room(?:s)?',
        r'parking(?:\s+available)?',
        r'disabled\s+access',
        r'wheelchair\s+accessible',
    ]
    
    patterns.extend(common_patterns)
    
    # Find matches
    for pattern in patterns:
        matches = re.findall(pattern, content_lower, re.IGNORECASE)
        if matches:
            # Get the original case version
            for match in re.finditer(pattern, content, re.IGNORECASE):
                attraction = match.group(0).strip()
                if len(attraction) > 3:  # Filter out very short matches
                    attractions.add(attraction.title())
    
    return sorted(list(attractions))


def extract_venue_details(content: str) -> Dict[str, List[str]]:
    """Extract comprehensive venue details from content."""
    
    # Age groups
    age_patterns = [
        r'all\s+ages?',
        r'family\s+friendly',
        r'(?:kids?|children)\s+welcome',
        r'adults?\s+only',
        r'18\+',
        r'under\s+\d+(?:s)?',
        r'\d+\s*years?\s*(?:and\s*)?(?:over|up)',
        r'junior\s+session(?:s)?',
        r'adult\s+session(?:s)?',
        r'toddler(?:s)?',
        r'teenager(?:s)?',
    ]
    
    age_groups = []
    for pattern in age_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        age_groups.extend(matches)
    
    # Pricing info
    pricing_patterns = [
        r'£\d+(?:\.\d{2})?(?:\s*per\s*(?:person|hour|game|session|day))?',
        r'from\s*£\d+(?:\.\d{2})?',
        r'starting\s*(?:at\s*)?£\d+(?:\.\d{2})?',
        r'prices?\s*from\s*£\d+(?:\.\d{2})?',
        r'group\s+rate(?:s)?',
        r'student\s+discount(?:s)?',
        r'family\s+ticket(?:s)?',
        r'season\s+pass(?:es)?',
        r'membership(?:s)?',
    ]
    
    pricing = []
    for pattern in pricing_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        pricing.extend(matches)
    
    # Party options
    party_patterns = [
        r'birthday\s+part(?:y|ies)',
        r'group\s+booking(?:s)?',
        r'corporate\s+event(?:s)?',
        r'team\s+building',
        r'hen\s+(?:do|party)',
        r'stag\s+(?:do|party)',
        r'private\s+hire',
        r'exclusive\s+use',
        r'party\s+package(?:s)?',
    ]
    
    party_options = []
    for pattern in party_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        party_options.extend(matches)
    
    # Special features
    special_patterns = [
        r'award[\-\s]?winning',
        r'unique',
        r'first\s+in\s+(?:uk|london|europe)',
        r'largest\s+in\s+(?:uk|london|europe)',
        r'biggest\s+in\s+(?:uk|london|europe)',
        r'multi[\-\s]?level',
        r'state[\-\s]?of[\-\s]?the[\-\s]?art',
        r'cutting[\-\s]?edge',
        r'immersive',
        r'themed',
    ]
    
    special_features = []
    for pattern in special_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        special_features.extend(matches)
    
    return {
        "age_groups": list(set(age_groups)),
        "pricing_info": list(set(pricing)),
        "party_options": list(set(party_options)),
        "special_features": list(set(special_features))
    }


def main():
    load_dotenv()
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise SystemExit("Missing EXA_API_KEY in environment or .env")
    
    exa = Exa(api_key)
    
    # Load existing venue data
    print("Loading venue data...")
    venues = []
    for filename in os.listdir("data"):
        if filename.startswith("places_") and filename.endswith(".json"):
            with open(f"data/{filename}", "r", encoding="utf-8") as f:
                data = json.load(f)
                for place in data.get("places", []):
                    if place.get("website") and place.get("name"):
                        venues.append({
                            "name": place["name"],
                            "category": data["category"],
                            "website": place["website"],
                            "address": place.get("address", ""),
                            "postcode": place.get("postcode", ""),
                            "rating": place.get("rating"),
                            "phone": place.get("phone", ""),
                        })
    
    # Get diverse sample
    sample = extract_diverse_venue_sample(venues, sample_size=15)
    print(f"Selected diverse sample of {len(sample)} venues across categories:")
    
    category_counts = {}
    for venue in sample:
        cat = venue["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    for cat, count in category_counts.items():
        print(f"  {cat}: {count}")
    
    # Create enhanced output directory
    out_dir = os.path.join("data", "enhanced_venue_profiles")
    os.makedirs(out_dir, exist_ok=True)
    
    # Process venues
    enhanced_profiles = []
    
    for i, venue in enumerate(sample):
        print(f"\nCrawling {i+1}/{len(sample)}: {venue['name']} ({venue['category']})")
        
        try:
            # Crawl content
            response = exa.get_contents(
                urls=[venue["website"]], 
                text=True,
                livecrawl="preferred",
                subpages=3,
                subpage_target=["about", "attractions", "activities", "prices", "facilities", "what-we-offer"],
                livecrawl_timeout=12000
            )
            
            content_parts = []
            for result in response.results:
                if result.text:
                    content_parts.append(result.text)
            
            if not content_parts:
                print(f"  No content found")
                continue
                
            content = "\n".join(content_parts)
            
            # Enhanced parsing
            attractions = enhanced_parse_attractions(content, venue["category"])
            details = extract_venue_details(content)
            
            # Create profile
            profile = {
                "name": venue["name"],
                "category": venue["category"],
                "website": venue["website"],
                "address": venue["address"],
                "postcode": venue["postcode"],
                "rating": venue["rating"],
                "phone": venue["phone"],
                "attractions": attractions,
                "age_groups": details["age_groups"],
                "pricing_info": details["pricing_info"][:10],  # Limit to avoid clutter
                "party_options": details["party_options"],
                "special_features": details["special_features"],
                "content_length": len(content),
                "content_summary": content[:800] + "..." if len(content) > 800 else content
            }
            
            # Save individual profile
            filename = f"enhanced_{i+1:02d}_{venue['name'].lower().replace(' ', '_').replace('/', '')[:25]}.json"
            with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            enhanced_profiles.append(profile)
            
            print(f"  Found {len(attractions)} attractions")
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    # Create comprehensive summary
    from collections import Counter
    
    all_attractions = []
    all_categories = []
    all_special_features = []
    
    for profile in enhanced_profiles:
        all_attractions.extend(profile["attractions"])
        all_categories.append(profile["category"])
        all_special_features.extend(profile["special_features"])
    
    summary = {
        "total_venues_enhanced": len(enhanced_profiles),
        "categories_covered": dict(Counter(all_categories)),
        "top_attractions": dict(Counter(all_attractions).most_common(25)),
        "special_features": dict(Counter(all_special_features).most_common(10)),
        "venues_by_category": {}
    }
    
    # Group venues by category for summary
    for profile in enhanced_profiles:
        cat = profile["category"]
        if cat not in summary["venues_by_category"]:
            summary["venues_by_category"][cat] = []
        
        summary["venues_by_category"][cat].append({
            "name": profile["name"],
            "attraction_count": len(profile["attractions"]),
            "top_attractions": profile["attractions"][:5],
            "website": profile["website"]
        })
    
    # Save summary
    with open(os.path.join(out_dir, "enhanced_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Enhanced crawling complete!")
    print(f"📁 Processed {len(enhanced_profiles)} venues")
    print(f"📊 Categories: {list(Counter(all_categories).keys())}")
    print(f"🎯 Top attractions found:")
    for attraction, count in Counter(all_attractions).most_common(8):
        print(f"   {attraction}: {count}")
    
    print(f"\n📄 Files saved to: {out_dir}")


if __name__ == "__main__":
    main()