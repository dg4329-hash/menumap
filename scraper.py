"""
MenuMap - NYU Dining Scraper
Fetches menu and nutritional data from dineoncampus API
"""

import requests
from datetime import datetime, timedelta
import json
import os

# DineOnCampus API base
API_BASE = "https://api.dineoncampus.com/v1"

# NYU site identifier (we need to discover this)
# From URL pattern: dineoncampus.com/NYUeats -> site name is "NYUeats"
SITE_NAME = "NYUeats"


def get_site_info(site_name: str) -> dict:
    """
    Get site information including site_id and available locations.
    """
    # Try different API patterns
    endpoints = [
        f"{API_BASE}/sites/{site_name}",
        f"{API_BASE}/site/{site_name}",
        f"https://api.dineoncampus.com/v1/sites/find?name={site_name}",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"[{response.status_code}] {endpoint}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error: {endpoint} - {e}")

    return None


def get_locations(site_id: str) -> list:
    """
    Get all dining locations for a site.
    """
    endpoint = f"{API_BASE}/locations/all_locations?site_id={site_id}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"[{response.status_code}] Locations endpoint")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error getting locations: {e}")

    return None


def get_menu(site_id: str, location_id: str, date: str = None) -> dict:
    """
    Get menu for a specific location and date.

    Args:
        site_id: The site identifier
        location_id: The dining hall location ID
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Try different endpoint patterns
    endpoints = [
        f"{API_BASE}/location/{location_id}/periods?platform=0&date={date}",
        f"{API_BASE}/location/menu?site_id={site_id}&location_id={location_id}&date={date}",
        f"https://new.dineoncampus.com/v1/location/menu.json?site_id={site_id}&location_id={location_id}&date={date}",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            print(f"[{response.status_code}] {endpoint[:80]}...")
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data
        except Exception as e:
            print(f"Error: {e}")

    return None


def discover_nyu_ids():
    """
    Attempt to discover NYU's site_id and location_ids by trying various API calls.
    """
    print("=" * 60)
    print("MenuMap - NYU Dining ID Discovery")
    print("=" * 60)

    # Known site slugs from URL
    site_slugs = ["NYUeats", "nyu", "nyueats"]

    for slug in site_slugs:
        print(f"\nTrying site slug: {slug}")
        info = get_site_info(slug)
        if info:
            print(f"Found site info: {json.dumps(info, indent=2)[:500]}")
            return info

    # If direct lookup fails, try to scrape from the webpage
    print("\nDirect API lookup failed. Will need to extract IDs from webpage...")
    return None


def scrape_all_menus(site_id: str, locations: list, date: str = None) -> list:
    """
    Scrape menus from all locations for a given date.
    """
    all_menus = []

    for location in locations:
        loc_id = location.get("id") or location.get("_id")
        loc_name = location.get("name", "Unknown")

        print(f"\nFetching menu for: {loc_name}")
        menu = get_menu(site_id, loc_id, date)

        if menu:
            all_menus.append({
                "location_id": loc_id,
                "location_name": loc_name,
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "menu_data": menu
            })

    return all_menus


def parse_menu_items(raw_menu: dict) -> list:
    """
    Parse raw API response into structured menu items with nutrition info.
    """
    items = []

    # The structure varies, but typically:
    # menu -> periods[] -> categories[] -> items[]

    periods = raw_menu.get("periods", [])
    if not periods and "menu" in raw_menu:
        periods = raw_menu["menu"].get("periods", [])

    for period in periods:
        period_name = period.get("name", "Unknown")  # Breakfast, Lunch, Dinner

        categories = period.get("categories", [])
        for category in categories:
            category_name = category.get("name", "Unknown")

            for item in category.get("items", []):
                parsed = {
                    "name": item.get("name", "Unknown"),
                    "description": item.get("desc", ""),
                    "period": period_name,
                    "category": category_name,
                    "portion": item.get("portion", ""),
                    "calories": None,
                    "protein": None,
                    "carbs": None,
                    "fat": None,
                    "dietary_tags": [],
                }

                # Extract nutrition
                nutrients = item.get("nutrients", [])
                for nutrient in nutrients:
                    name = nutrient.get("name", "").lower()
                    value = nutrient.get("value", 0)

                    if "calorie" in name:
                        parsed["calories"] = value
                    elif "protein" in name:
                        parsed["protein"] = value
                    elif "carb" in name:
                        parsed["carbs"] = value
                    elif "fat" in name and "saturated" not in name and "trans" not in name:
                        parsed["fat"] = value

                # Extract dietary tags
                filters = item.get("filters", [])
                for f in filters:
                    if f.get("name"):
                        parsed["dietary_tags"].append(f["name"])

                # Also check for direct flags
                if item.get("vegetarian"):
                    parsed["dietary_tags"].append("Vegetarian")
                if item.get("vegan"):
                    parsed["dietary_tags"].append("Vegan")
                if item.get("gluten_free"):
                    parsed["dietary_tags"].append("Gluten-Free")

                items.append(parsed)

    return items


if __name__ == "__main__":
    # Step 1: Discover NYU IDs
    result = discover_nyu_ids()

    if result:
        print("\n" + "=" * 60)
        print("SUCCESS - Found NYU dining data!")
        print("=" * 60)
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 60)
        print("Need to extract IDs manually from webpage")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Open browser DevTools on dineoncampus.com/NYUeats")
        print("2. Go to Network tab, filter by XHR/Fetch")
        print("3. Click on a dining hall to see API calls")
        print("4. Extract site_id and location_id from the requests")
