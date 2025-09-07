#!/usr/bin/env python3
"""
Crawl venue websites from Google Places data and extract detailed attraction information.

Uses Exa to crawl each venue's website and parse specific activities, attractions,
pricing, facilities, and services offered at each location.
"""
import json
import os
import re
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from exa_py import Exa


@dataclass 
class VenueProfile:
    name: str
    category: str
    website: str
    address: str
    postcode: str
    rating: Optional[float]
    phone: Optional[str]
    attractions: List[str]
    facilities: List[str]
    pricing_info: List[str]
    age_groups: List[str]
    party_options: List[str]
    special_features: List[str]
    opening_hours: Optional[str]
    content_summary: str


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def extract_venues_with_websites() -> List[Dict[str, Any]]:
    """Extract all venues with websites from Google Places data."""
    venues = []
    
    for path in os.listdir("data"):
        if not path.startswith("places_") or not path.endswith(".json"):
            continue
            
        with open(os.path.join("data", path), "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for place in data.get("places", []):
            if place.get("website") and place.get("name"):
                venues.append({
                    "name": place.get("name"),
                    "category": data.get("category"),
                    "website": place.get("website"),
                    "address": place.get("address", ""),
                    "postcode": place.get("postcode", ""),
                    "rating": place.get("rating"),
                    "phone": place.get("phone", ""),
                })
    
    return venues


def parse_attractions(content: str) -> List[str]:
    """Parse specific attractions and activities from venue content."""
    content_lower = content.lower()
    
    # Entertainment activity keywords to look for
    activity_patterns = [
        # Bowling specific
        r'(\d+)\s*(?:pin\s*)?bowling\s*lanes?',
        r'ten\s*pin\s*bowling',
        r'cosmic\s*bowling',
        r'glow\s*bowling',
        
        # Karting specific  
        r'indoor\s*karting',
        r'outdoor\s*karting',
        r'electric\s*karts?',
        r'petrol\s*karts?',
        r'junior\s*karting',
        
        # Trampoline specific
        r'main\s*court',
        r'foam\s*pit',
        r'dodgeball\s*courts?',
        r'basketball\s*hoops?',
        r'battle\s*beam',
        r'ninja\s*course',
        r'wipe\s*out',
        r'slam\s*dunk',
        
        # Laser tag specific
        r'laser\s*tag\s*arenas?',
        r'multi\s*level\s*arena',
        r'outdoor\s*laser',
        r'tactical\s*laser',
        
        # VR specific
        r'vr\s*experiences?',
        r'virtual\s*reality\s*games?',
        r'multiplayer\s*vr',
        r'vr\s*escape',
        r'vr\s*zombies?',
        
        # Escape rooms specific
        r'escape\s*rooms?\s*themes?',
        r'horror\s*escape',
        r'mystery\s*rooms?',
        r'puzzle\s*rooms?',
        
        # Climbing specific
        r'bouldering\s*walls?',
        r'top\s*rope\s*climbing',
        r'lead\s*climbing',
        r'auto\s*belay',
        r'climbing\s*grades?',
        
        # Axe throwing specific
        r'axe\s*throwing\s*lanes?',
        r'hatchet\s*throwing',
        r'tomahawk\s*throwing',
        
        # General amenities
        r'party\s*rooms?',
        r'private\s*hire',
        r'birthday\s*parties',
        r'corporate\s*events?',
        r'team\s*building',
        r'group\s*bookings?',
        r'food\s*and\s*drink',
        r'cafe',
        r'restaurant',
        r'bar\s*area',
        r'parking\s*available',
        r'accessible',
        r'disabled\s*access',
    ]
    
    attractions = []
    for pattern in activity_patterns:
        matches = re.findall(pattern, content_lower, re.IGNORECASE)
        for match in matches:
            # Clean up the match text
            if isinstance(match, tuple):
                match_text = ' '.join(str(m) for m in match if m)
            else:
                match_text = str(match)
            
            # Find the actual text around the match for context
            pattern_obj = re.compile(pattern, re.IGNORECASE)
            full_matches = pattern_obj.findall(content)
            if full_matches:
                attractions.extend([m if isinstance(m, str) else ' '.join(str(x) for x in m if x) 
                                 for m in full_matches])
    
    return list(set(attractions))  # Remove duplicates


def parse_facilities(content: str) -> List[str]:
    """Parse facilities and amenities from venue content."""
    content_lower = content.lower()
    
    facility_patterns = [
        r'parking',
        r'disabled\s*access',
        r'wheelchair\s*accessible',
        r'cafe',
        r'restaurant',
        r'bar',
        r'lockers?',
        r'changing\s*rooms?',
        r'toilets?',
        r'party\s*rooms?',
        r'meeting\s*rooms?',
        r'spectator\s*areas?',
        r'viewing\s*areas?',
        r'shop',
        r'reception',
        r'air\s*conditioning',
        r'heating',
        r'wifi',
        r'sound\s*system',
        r'lighting\s*effects?',
    ]
    
    facilities = []
    for pattern in facility_patterns:
        if re.search(pattern, content_lower):
            # Extract the actual facility name from the pattern
            facility_name = pattern.replace(r'\s*', ' ').replace('?', '').replace(r'\\', '')
            facilities.append(facility_name.title())
    
    return list(set(facilities))


def parse_pricing_info(content: str) -> List[str]:
    """Extract pricing information from venue content."""
    pricing_patterns = [
        r'£\d+(?:\.\d{2})?(?:\s*per\s*(?:person|hour|game|session))?',
        r'from\s*£\d+',
        r'starting\s*at\s*£\d+',
        r'prices?\s*from\s*£\d+',
        r'group\s*rates?',
        r'student\s*discount',
        r'family\s*tickets?',
        r'season\s*passes?',
    ]
    
    pricing = []
    for pattern in pricing_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        pricing.extend(matches)
    
    return list(set(pricing))


def parse_age_groups(content: str) -> List[str]:
    """Extract age group information from venue content."""
    age_patterns = [
        r'all\s*ages?',
        r'family\s*friendly',
        r'kids?\s*welcome',
        r'children\s*welcome', 
        r'adults?\s*only',
        r'18\+',
        r'under\s*\d+s?',
        r'\d+\s*years?\s*and\s*over',
        r'junior\s*sessions?',
        r'adult\s*sessions?',
        r'toddlers?',
        r'teenagers?',
    ]
    
    age_groups = []
    for pattern in age_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        age_groups.extend(matches)
    
    return list(set(age_groups))


def crawl_venue_content(exa: Exa, venue: Dict[str, Any]) -> Optional[str]:
    """Crawl a single venue's website content using Exa."""
    try:
        # Use Exa contents API to get full page text
        response = exa.get_contents(
            urls=[venue["website"]], 
            text=True,
            livecrawl="preferred",
            subpages=2,  # Get main page + up to 2 subpages
            subpage_target=["about", "attractions", "activities", "prices", "facilities"],
            livecrawl_timeout=10000
        )
        
        content_parts = []
        for result in response.results:
            if result.text:
                content_parts.append(result.text)
        
        return "\n".join(content_parts) if content_parts else None
        
    except Exception as e:
        print(f"Error crawling {venue['name']}: {e}")
        return None


def create_venue_profile(venue: Dict[str, Any], content: str) -> VenueProfile:
    """Create a comprehensive venue profile from crawled content."""
    
    attractions = parse_attractions(content)
    facilities = parse_facilities(content)
    pricing = parse_pricing_info(content)
    age_groups = parse_age_groups(content)
    
    # Extract party options
    party_patterns = [
        r'birthday\s*parties',
        r'group\s*bookings?',
        r'corporate\s*events?',
        r'team\s*building',
        r'hen\s*(?:do|party)',
        r'stag\s*(?:do|party)',
        r'private\s*hire',
        r'exclusive\s*use',
    ]
    
    party_options = []
    for pattern in party_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        party_options.extend(matches)
    
    # Extract special features
    special_patterns = [
        r'award\s*winning',
        r'unique',
        r'first\s*in\s*(?:uk|london)',
        r'largest\s*in\s*(?:uk|london)',
        r'multi\s*level',
        r'state\s*of\s*the\s*art',
        r'cutting\s*edge',
        r'immersive',
        r'themed',
    ]
    
    special_features = []
    for pattern in special_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        special_features.extend(matches)
    
    # Create summary (first 500 chars of content, cleaned)
    clean_content = re.sub(r'\s+', ' ', content).strip()
    summary = clean_content[:500] + "..." if len(clean_content) > 500 else clean_content
    
    return VenueProfile(
        name=venue["name"],
        category=venue["category"],
        website=venue["website"],
        address=venue["address"],
        postcode=venue["postcode"],
        rating=venue["rating"],
        phone=venue["phone"],
        attractions=attractions,
        facilities=facilities,
        pricing_info=pricing,
        age_groups=age_groups,
        party_options=party_options,
        special_features=special_features,
        opening_hours=None,  # Could extract from content if needed
        content_summary=summary
    )


def main():
    load_dotenv()
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        raise SystemExit("Missing EXA_API_KEY in environment or .env")
    
    exa = Exa(api_key)
    
    # Extract venues with websites
    print("Extracting venues with websites...")
    venues = extract_venues_with_websites()
    print(f"Found {len(venues)} venues with websites")
    
    # Create output directory
    out_dir = os.path.join(os.getcwd(), "data", "venue_profiles")
    ensure_dir(out_dir)
    
    # Process venues in batches to manage API costs
    batch_size = 20  # Adjust based on budget
    processed_venues = []
    
    print(f"Processing first {batch_size} venues (adjust batch_size for more)...")
    
    for i, venue in enumerate(venues[:batch_size]):
        print(f"Crawling {i+1}/{batch_size}: {venue['name']}")
        
        # Crawl venue content
        content = crawl_venue_content(exa, venue)
        if not content:
            print(f"  No content found for {venue['name']}")
            continue
        
        # Create venue profile
        profile = create_venue_profile(venue, content)
        
        # Save individual venue profile
        profile_dict = {
            "name": profile.name,
            "category": profile.category,
            "website": profile.website,
            "address": profile.address,
            "postcode": profile.postcode,
            "rating": profile.rating,
            "phone": profile.phone,
            "attractions": profile.attractions,
            "facilities": profile.facilities,
            "pricing_info": profile.pricing_info,
            "age_groups": profile.age_groups,
            "party_options": profile.party_options,
            "special_features": profile.special_features,
            "content_summary": profile.content_summary,
        }
        
        filename = f"venue_{i+1:03d}_{venue['name'].lower().replace(' ', '_').replace('/', '_')[:30]}.json"
        filepath = os.path.join(out_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile_dict, f, indent=2, ensure_ascii=False)
        
        processed_venues.append(profile_dict)
        
        # Small delay to respect rate limits
        time.sleep(0.2)
    
    # Create summary report
    summary = {
        "total_venues_crawled": len(processed_venues),
        "total_venues_available": len(venues),
        "categories": {},
        "top_attractions": {},
        "top_facilities": {},
    }
    
    # Analyze results
    from collections import Counter
    
    category_counts = Counter(v["category"] for v in processed_venues)
    all_attractions = [a for v in processed_venues for a in v["attractions"]]
    all_facilities = [f for v in processed_venues for f in v["facilities"]]
    
    summary["categories"] = dict(category_counts)
    summary["top_attractions"] = dict(Counter(all_attractions).most_common(20))
    summary["top_facilities"] = dict(Counter(all_facilities).most_common(15))
    
    # Save summary
    with open(os.path.join(out_dir, "venue_profiles_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nCompleted! Processed {len(processed_venues)} venues")
    print(f"Files saved to: {out_dir}")
    print(f"Categories covered: {list(category_counts.keys())}")
    print(f"Most common attractions: {list(Counter(all_attractions).most_common(5))}")


if __name__ == "__main__":
    main()