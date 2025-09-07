#!/usr/bin/env python3
"""
Convert the master CSV to JSON format for the Google Maps display.
Only includes venues with valid coordinates.
"""

import csv
import json
import sys
from pathlib import Path

def convert_csv_to_json():
    """Convert the master CSV to JSON format for map display"""
    
    # File paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    csv_file = project_dir / "data" / "london_lbe_master.csv"
    json_file = project_dir / "venue_data.json"
    
    if not csv_file.exists():
        print(f"Error: {csv_file} not found")
        sys.exit(1)
    
    venues = []
    skipped_count = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Skip venues without coordinates
            if not row.get('lat') or not row.get('lon'):
                skipped_count += 1
                continue
            
            # Skip invalid coordinates
            try:
                lat = float(row['lat'])
                lon = float(row['lon'])
                
                # Basic sanity check for London area
                if not (50.5 < lat < 52.0 and -1.0 < lon < 1.0):
                    skipped_count += 1
                    continue
                    
            except ValueError:
                skipped_count += 1
                continue
            
            # Create venue object
            venue = {
                'source': row.get('source', ''),
                'category': row.get('category', ''),
                'name': row.get('name', ''),
                'brand': row.get('brand', ''),
                'url': row.get('url', ''),
                'postcode': row.get('postcode', ''),
                'lat': lat,
                'lon': lon,
                'phone': row.get('phone', ''),
                'rating': row.get('rating', ''),
                'price_level': row.get('price_level', ''),
                'business_status': row.get('business_status', ''),
                'opening_hours': row.get('opening_hours', '')
            }
            
            # Clean empty string values
            venue = {k: v for k, v in venue.items() if v and v != ''}
            
            venues.append(venue)
    
    # Write JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(venues, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(venues)} venues to {json_file}")
    print(f"Skipped {skipped_count} venues without valid coordinates")
    
    # Print category summary
    category_counts = {}
    for venue in venues:
        cat = venue.get('category', 'unknown')
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("\nVenues by category:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")

if __name__ == "__main__":
    convert_csv_to_json()