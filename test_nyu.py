"""
Quick test to pull NYU dining data using fastdine approach
"""
import sys
sys.path.insert(0, '../fastdine_source')

from fastdine.site import Site
from datetime import date

print("=" * 60)
print("MenuMap - NYU Dining Data Test")
print("=" * 60)

# Initialize NYU site
print("\nConnecting to NYUeats...")
try:
    nyu = Site("NYUeats")
    print(f"SUCCESS! Connected to: {nyu.name}")
    print(f"Site ID: {nyu.id}")

    print(f"\nFound {len(nyu.locations)} dining locations:")
    print("-" * 40)
    for loc in nyu.locations:
        print(f"  - {loc.name} (ID: {loc.id})")

    # Try to get today's menu from first location
    if nyu.locations:
        test_loc = nyu.locations[0]
        today = date.today()
        print(f"\nFetching menu for '{test_loc.name}' on {today}...")

        try:
            menu = test_loc.get_menu(today)
            print(f"Got menu with {len(menu.periods)} periods")

            for period in menu.periods:
                print(f"\n  [{period.name}]")
                for cat in period.categories[:2]:  # First 2 categories
                    print(f"    {cat.name}:")
                    for item in cat.items[:3]:  # First 3 items
                        calories = item.nutrients_by_name.get('Calories', None)
                        cal_str = f" ({calories.value} cal)" if calories else ""
                        print(f"      - {item.name}{cal_str}")

        except Exception as e:
            print(f"Could not get menu: {e}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
