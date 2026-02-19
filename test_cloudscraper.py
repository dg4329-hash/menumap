"""
Test NYU dining API using cloudscraper (bypasses Cloudflare)
Based on DISH-API approach
"""
import cloudscraper
from fake_useragent import UserAgent
import json
import time

# Initialize scraper
scraper = cloudscraper.create_scraper()
ua = UserAgent()

API_BASE = "https://api.dineoncampus.com/v1/"

def fetch(endpoint):
    """Fetch from API with Cloudflare bypass"""
    url = API_BASE + endpoint
    headers = {"User-Agent": ua.random}

    print(f"Fetching: {url[:80]}...")
    response = scraper.get(url, headers=headers, timeout=30)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text[:200]}")
        return None

print("=" * 60)
print("MenuMap - NYU Dining Test (cloudscraper)")
print("=" * 60)

# Step 1: Get NYU site info
print("\n[1] Getting NYU site info...")
site_info = fetch("sites/NYUeats/info")

if site_info and site_info.get("status") == "success":
    site = site_info["site"]
    site_id = site["id"]
    print(f"SUCCESS! Site: {site['name']} (ID: {site_id})")

    # Step 2: Get all locations
    print("\n[2] Getting dining locations...")
    time.sleep(1)

    locations = fetch(f"locations/all_locations?platform=0&site_id={site_id}&for_menus=true&with_buildings=true")

    if locations and locations.get("status") == "success":
        all_locations = []

        # Locations from buildings
        for building in locations.get("buildings", []):
            for loc in building.get("locations", []):
                all_locations.append(loc)

        # Standalone locations
        for loc in locations.get("locations", []):
            if loc["id"] not in [l["id"] for l in all_locations]:
                all_locations.append(loc)

        print(f"Found {len(all_locations)} locations:")
        for loc in all_locations:
            print(f"  - {loc['name']}")

        # Step 3: Get menu for first location
        if all_locations:
            test_loc = all_locations[0]
            print(f"\n[3] Getting today's menu for '{test_loc['name']}'...")
            time.sleep(1)

            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")

            periods_resp = fetch(f"location/{test_loc['id']}/periods?platform=0&date={today}")

            if periods_resp and periods_resp.get("status") == "success":
                periods = periods_resp.get("periods", [])
                print(f"Found {len(periods)} meal periods: {[p['name'] for p in periods]}")

                for period in periods[:1]:  # Just first period for test
                    print(f"\n--- {period['name'].upper()} ---")
                    time.sleep(1)

                    menu_resp = fetch(f"location/{test_loc['id']}/periods/{period['id']}?platform=0&date={today}")

                    if menu_resp and "menu" in menu_resp:
                        menu = menu_resp["menu"]

                        # Debug: print structure
                        print(f"Menu keys: {menu.keys()}")

                        # Get periods from menu
                        menu_periods = menu.get("periods", {})

                        # Handle if periods is a dict with categories directly
                        if isinstance(menu_periods, dict):
                            categories = menu_periods.get("categories", [])
                        elif isinstance(menu_periods, list) and len(menu_periods) > 0:
                            categories = menu_periods[0].get("categories", [])
                        else:
                            categories = []

                        print(f"Found {len(categories)} categories")

                        for cat in categories[:3]:
                            print(f"\n  {cat['name']}:")
                            for item in cat.get("items", [])[:5]:
                                # Get nutritional info
                                nutrients = item.get("nutrients", [])
                                cal = next((n["value"] for n in nutrients if "calorie" in n.get("name", "").lower()), "?")
                                protein = next((n["value"] for n in nutrients if n.get("name", "").lower() == "protein"), "?")

                                # Get dietary tags
                                filters = [f["name"] for f in item.get("filters", [])]
                                tags = ", ".join(filters) if filters else ""

                                print(f"    - {item['name']}")
                                print(f"      Calories: {cal} | Protein: {protein}g | Tags: {tags or 'none'}")

            else:
                print("Could not get periods")
    else:
        print("Could not get locations")
else:
    print("Could not get site info")
