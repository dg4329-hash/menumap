"""
MenuMap - NYU Dining Scraper
Fetches all menu data from NYU dining locations and stores in SQLite
"""
import cloudscraper
from fake_useragent import UserAgent
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

# Config
API_BASE = "https://api.dineoncampus.com/v1/"
NYU_SITE_NAME = "NYUeats"
REQUEST_DELAY = 1.5  # seconds between requests
DB_PATH = Path(__file__).parent / "menumap.db"

# Initialize scraper
scraper = cloudscraper.create_scraper()
ua = UserAgent()


def fetch(endpoint: str) -> dict | None:
    """Fetch from API with Cloudflare bypass"""
    url = API_BASE + endpoint
    headers = {"User-Agent": ua.random}

    try:
        response = scraper.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  Error {response.status_code}: {endpoint[:50]}")
            return None
    except Exception as e:
        print(f"  Request failed: {e}")
        return None


def init_database():
    """Create database tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Locations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            building TEXT
        )
    ''')

    # Menu items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id TEXT NOT NULL,
            date TEXT NOT NULL,
            period TEXT NOT NULL,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            calories INTEGER,
            protein REAL,
            carbs REAL,
            fat REAL,
            fiber REAL,
            sugar REAL,
            saturated_fat REAL,
            trans_fat REAL,
            cholesterol REAL,
            sodium REAL,
            potassium REAL,
            calcium REAL,
            iron REAL,
            vitamin_d REAL,
            vitamin_c REAL,
            vitamin_a REAL,
            dietary_tags TEXT,
            allergens TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(id),
            UNIQUE(location_id, date, period, category, name)
        )
    ''')

    # Add new columns to existing database if they don't exist
    new_columns = [
        ('fiber', 'REAL'), ('sugar', 'REAL'), ('saturated_fat', 'REAL'),
        ('trans_fat', 'REAL'), ('cholesterol', 'REAL'), ('sodium', 'REAL'),
        ('potassium', 'REAL'), ('calcium', 'REAL'), ('iron', 'REAL'),
        ('vitamin_d', 'REAL'), ('vitamin_c', 'REAL'), ('vitamin_a', 'REAL')
    ]
    for col_name, col_type in new_columns:
        try:
            c.execute(f'ALTER TABLE menu_items ADD COLUMN {col_name} {col_type}')
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Index for fast queries
    c.execute('CREATE INDEX IF NOT EXISTS idx_menu_date ON menu_items(date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_menu_location ON menu_items(location_id)')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


def get_site_info() -> tuple[str, list]:
    """Get NYU site ID and all dining locations"""
    print("Fetching NYU site info...")
    site_info = fetch(f"sites/{NYU_SITE_NAME}/info")

    if not site_info or site_info.get("status") != "success":
        raise Exception("Could not fetch site info")

    site_id = site_info["site"]["id"]
    print(f"  Site ID: {site_id}")

    time.sleep(REQUEST_DELAY)

    # Get locations
    print("Fetching dining locations...")
    loc_resp = fetch(f"locations/all_locations?platform=0&site_id={site_id}&for_menus=true&with_buildings=true")

    if not loc_resp or loc_resp.get("status") != "success":
        raise Exception("Could not fetch locations")

    locations = []

    # Extract from buildings
    for building in loc_resp.get("buildings", []):
        building_name = building.get("name", "Unknown")
        for loc in building.get("locations", []):
            locations.append({
                "id": loc["id"],
                "name": loc["name"],
                "building": building_name
            })

    # Standalone locations
    existing_ids = {l["id"] for l in locations}
    for loc in loc_resp.get("locations", []):
        if loc["id"] not in existing_ids:
            locations.append({
                "id": loc["id"],
                "name": loc["name"],
                "building": None
            })

    print(f"  Found {len(locations)} locations")
    return site_id, locations


def save_locations(locations: list):
    """Save locations to database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for loc in locations:
        c.execute('''
            INSERT OR REPLACE INTO locations (id, name, building)
            VALUES (?, ?, ?)
        ''', (loc["id"], loc["name"], loc["building"]))

    conn.commit()
    conn.close()


def parse_nutrients(nutrients: list) -> dict:
    """Extract all nutrients from API response"""
    result = {
        "calories": None, "protein": None, "carbs": None, "fat": None,
        "fiber": None, "sugar": None, "saturated_fat": None, "trans_fat": None,
        "cholesterol": None, "sodium": None, "potassium": None,
        "calcium": None, "iron": None, "vitamin_d": None, "vitamin_c": None, "vitamin_a": None
    }

    for n in nutrients:
        name = n.get("name", "").lower()
        # Use value_numeric if available, otherwise value
        value = n.get("value_numeric") or n.get("value")

        if value is None:
            continue

        # Handle string values like "25" or "25g" or "0+" or "-"
        if isinstance(value, str):
            if value == "-" or value == "":
                continue
            # Remove non-numeric chars except decimal point
            value = ''.join(c for c in value if c.isdigit() or c == '.')
            if value:
                try:
                    value = float(value)
                except ValueError:
                    value = None

        if value is None:
            continue

        # Match nutrient names (API returns "Protein (g)", "Total Fat (g)", etc.)
        if name == "calories":
            result["calories"] = int(value)
        elif "protein" in name and "(" in name:  # "Protein (g)"
            result["protein"] = value
        elif "total carbohydrate" in name:  # "Total Carbohydrates (g)"
            result["carbs"] = value
        elif name == "total fat (g)":  # Exact match for total fat
            result["fat"] = value
        elif name == "dietary fiber (g)":
            result["fiber"] = value
        elif name == "sugar (g)":
            result["sugar"] = value
        elif name == "saturated fat (g)":
            result["saturated_fat"] = value
        elif name == "trans fat (g)":
            result["trans_fat"] = value
        elif name == "cholesterol (mg)":
            result["cholesterol"] = value
        elif name == "sodium (mg)":
            result["sodium"] = value
        elif name == "potassium (mg)":
            result["potassium"] = value
        elif name == "calcium (mg)":
            result["calcium"] = value
        elif name == "iron (mg)":
            result["iron"] = value
        elif "vitamin d" in name:
            result["vitamin_d"] = value
        elif "vitamin c" in name:
            result["vitamin_c"] = value
        elif "vitamin a" in name:
            result["vitamin_a"] = value

    return result


def scrape_location_menu(location: dict, date: str) -> list:
    """Scrape all menu items for a location on a given date"""
    items = []

    # Get periods
    periods_resp = fetch(f"location/{location['id']}/periods?platform=0&date={date}")
    time.sleep(REQUEST_DELAY)

    if not periods_resp or periods_resp.get("status") != "success":
        return items

    if periods_resp.get("closed", False):
        print(f"    {location['name']}: CLOSED")
        return items

    periods = periods_resp.get("periods", [])

    for period in periods:
        period_name = period["name"]

        # Get detailed menu
        menu_resp = fetch(f"location/{location['id']}/periods/{period['id']}?platform=0&date={date}")
        time.sleep(REQUEST_DELAY)

        if not menu_resp or "menu" not in menu_resp:
            continue

        menu = menu_resp["menu"]
        menu_periods = menu.get("periods", {})

        # Handle different response formats
        if isinstance(menu_periods, dict):
            categories = menu_periods.get("categories", [])
        elif isinstance(menu_periods, list) and len(menu_periods) > 0:
            categories = menu_periods[0].get("categories", [])
        else:
            continue

        for cat in categories:
            category_name = cat.get("name", "Other")

            for item in cat.get("items", []):
                nutrients = parse_nutrients(item.get("nutrients", []))

                # Extract dietary tags and allergens
                filters = item.get("filters", [])
                dietary_tags = []
                allergens = []

                for f in filters:
                    fname = f.get("name", "")
                    # Common dietary tags
                    if fname in ["Vegan", "Vegetarian", "Avoiding Gluten", "Halal", "Kosher"]:
                        dietary_tags.append(fname)
                    elif fname.startswith("Good Source"):
                        dietary_tags.append(fname)
                    else:
                        # Likely an allergen
                        allergens.append(fname)

                items.append({
                    "location_id": location["id"],
                    "date": date,
                    "period": period_name,
                    "category": category_name,
                    "name": item.get("name", "Unknown"),
                    "description": item.get("desc", ""),
                    "calories": nutrients["calories"],
                    "protein": nutrients["protein"],
                    "carbs": nutrients["carbs"],
                    "fat": nutrients["fat"],
                    "fiber": nutrients["fiber"],
                    "sugar": nutrients["sugar"],
                    "saturated_fat": nutrients["saturated_fat"],
                    "trans_fat": nutrients["trans_fat"],
                    "cholesterol": nutrients["cholesterol"],
                    "sodium": nutrients["sodium"],
                    "potassium": nutrients["potassium"],
                    "calcium": nutrients["calcium"],
                    "iron": nutrients["iron"],
                    "vitamin_d": nutrients["vitamin_d"],
                    "vitamin_c": nutrients["vitamin_c"],
                    "vitamin_a": nutrients["vitamin_a"],
                    "dietary_tags": ",".join(dietary_tags),
                    "allergens": ",".join(allergens)
                })

    return items


def save_menu_items(items: list):
    """Save menu items to database"""
    if not items:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for item in items:
        try:
            c.execute('''
                INSERT OR REPLACE INTO menu_items
                (location_id, date, period, category, name, description,
                 calories, protein, carbs, fat, fiber, sugar, saturated_fat,
                 trans_fat, cholesterol, sodium, potassium, calcium, iron,
                 vitamin_d, vitamin_c, vitamin_a, dietary_tags, allergens)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item["location_id"], item["date"], item["period"],
                item["category"], item["name"], item["description"],
                item["calories"], item["protein"], item["carbs"], item["fat"],
                item["fiber"], item["sugar"], item["saturated_fat"],
                item["trans_fat"], item["cholesterol"], item["sodium"],
                item["potassium"], item["calcium"], item["iron"],
                item["vitamin_d"], item["vitamin_c"], item["vitamin_a"],
                item["dietary_tags"], item["allergens"]
            ))
        except sqlite3.Error as e:
            print(f"    Error saving item: {e}")

    conn.commit()
    conn.close()


def scrape_all(date: str = None):
    """Main scraping function - fetches all menus for all locations"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print(f"MenuMap Scraper - {date}")
    print("=" * 60)

    # Initialize
    init_database()

    # Get site and locations
    site_id, locations = get_site_info()
    save_locations(locations)

    # Scrape each location
    total_items = 0
    for i, loc in enumerate(locations, 1):
        print(f"\n[{i}/{len(locations)}] {loc['name']}...")

        items = scrape_location_menu(loc, date)
        save_menu_items(items)

        print(f"    Saved {len(items)} items")
        total_items += len(items)

    print("\n" + "=" * 60)
    print(f"COMPLETE: {total_items} total items saved to {DB_PATH}")
    print("=" * 60)


def get_stats():
    """Print database statistics"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM locations")
    loc_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM menu_items")
    item_count = c.fetchone()[0]

    c.execute("SELECT DISTINCT date FROM menu_items ORDER BY date DESC LIMIT 5")
    dates = [r[0] for r in c.fetchall()]

    conn.close()

    print(f"\nDatabase Stats:")
    print(f"  Locations: {loc_count}")
    print(f"  Menu Items: {item_count}")
    print(f"  Recent dates: {dates}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        get_stats()
    else:
        # Scrape today's menus
        scrape_all()
        get_stats()
