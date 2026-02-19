"""
MenuMap - Database Query Tools
Functions that the AI can call to search the menu database
"""
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime

DB_PATH = Path(__file__).parent / "menumap.db"

# Dining hall hours (Official NYU hours from nyu.edu)
# Format: {location_name: {day_type: {period: (start, end)}}}
# day_type: "weekday" (Mon-Thu), "friday", "saturday", "sunday"
DINING_HOURS = {
    "NYU EATS at Downstein": {
        "weekday": {
            "Breakfast": ("7:00 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
        "friday": {
            "Breakfast": ("7:00 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
        "saturday": {
            "Brunch": ("9:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
        "sunday": {
            "Brunch": ("9:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
    },
    "NYU EATS at Third North": {
        "weekday": {
            "Breakfast": ("7:30 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
        "friday": {
            "Breakfast": ("7:30 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
        "saturday": {
            "Brunch": ("10:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
        "sunday": {
            "Brunch": ("10:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
    },
    "NYU EATS at Lipton": {
        "weekday": {
            "Breakfast": ("7:30 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
        "friday": {
            "Breakfast": ("7:30 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "9:00 PM"),
        },
        "saturday": {
            "Brunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "8:00 PM"),
        },
        "sunday": {
            "Brunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "8:00 PM"),
        },
    },
    "The Marketplace at Kimmel": {
        "weekday": {
            "Breakfast": ("7:30 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "8:00 PM"),
        },
        "friday": {
            "Breakfast": ("7:30 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("4:00 PM", "8:00 PM"),
        },
        "saturday": None,  # Closed
        "sunday": None,    # Closed
    },
    "Palladium": {
        "weekday": {
            "Dinner": ("4:00 PM", "10:00 PM"),
        },
        "friday": {
            "Dinner": ("4:00 PM", "10:00 PM"),
        },
        "saturday": {
            "Dinner": ("4:00 PM", "10:00 PM"),
        },
        "sunday": {
            "Brunch": ("11:00 AM", "3:00 PM"),
            "Dinner": ("5:00 PM", "10:00 PM"),
        },
    },
    "Crave NYU": {
        "weekday": {"All Day": ("10:30 AM", "8:30 PM")},
        "friday": {"All Day": ("10:30 AM", "8:30 PM")},
        "saturday": {"All Day": ("10:30 AM", "8:30 PM")},
        "sunday": {"All Day": ("10:30 AM", "8:30 PM")},
    },
    "Upstein": {
        "weekday": {"All Day": ("10:30 AM", "10:00 PM")},
        "friday": {"All Day": ("10:30 AM", "8:00 PM")},
        "saturday": None,  # Closed
        "sunday": None,    # Closed
    },
    "Kosher Eatery": {
        "weekday": {"All Day": ("11:30 AM", "7:30 PM")},
        "friday": {"All Day": ("11:30 AM", "2:00 PM")},
        "saturday": None,  # Closed
        "sunday": {"All Day": ("12:30 PM", "7:30 PM")},
    },
    "Jasper Kane Cafe": {
        "weekday": {
            "Breakfast": ("7:30 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
        },
        "friday": {
            "Breakfast": ("7:30 AM", "10:30 AM"),
            "Lunch": ("11:00 AM", "3:00 PM"),
        },
        "saturday": None,
        "sunday": None,
    },
    "Starbucks": {
        "weekday": {"All Day": ("7:00 AM", "9:00 PM")},
        "friday": {"All Day": ("7:00 AM", "9:00 PM")},
        "saturday": {"All Day": ("8:00 AM", "8:00 PM")},
        "sunday": {"All Day": ("8:00 AM", "8:00 PM")},
    },
    "Dunkin'": {
        "weekday": {"All Day": ("7:00 AM", "8:00 PM")},
        "friday": {"All Day": ("7:00 AM", "8:00 PM")},
        "saturday": {"All Day": ("8:00 AM", "6:00 PM")},
        "sunday": {"All Day": ("8:00 AM", "6:00 PM")},
    },
    "U-Hall Commons Cafe": {
        "weekday": {"Dinner": ("5:00 PM", "11:00 PM")},
        "friday": {"Dinner": ("5:00 PM", "11:00 PM")},
        "saturday": None,  # Closed
        "sunday": None,    # Closed
    },
    "Peet's Coffee": {
        "weekday": {"All Day": ("7:45 AM", "5:00 PM")},
        "friday": {"All Day": ("7:45 AM", "2:00 PM")},
        "saturday": None,  # Closed
        "sunday": None,    # Closed
    },
    "Flavor Lab by NYU Eats": {
        "weekday": {"All Day": ("11:00 AM", "8:00 PM")},
        "friday": {"All Day": ("11:00 AM", "8:00 PM")},
        "saturday": {"All Day": ("11:00 AM", "8:00 PM")},
        "sunday": {"All Day": ("11:00 AM", "8:00 PM")},
    },
}


def _get_day_type() -> str:
    """Get the current day type for hours lookup"""
    day = datetime.now().weekday()  # 0=Monday, 6=Sunday
    if day < 4:  # Mon-Thu
        return "weekday"
    elif day == 4:  # Friday
        return "friday"
    elif day == 5:  # Saturday
        return "saturday"
    else:  # Sunday
        return "sunday"


def get_current_time() -> dict:
    """
    Get the current date, time, and day of week.
    Use this to provide context-aware recommendations.

    Returns:
        Dict with current time info
    """
    now = datetime.now()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    return {
        "current_time": now.strftime("%I:%M %p"),
        "day_of_week": day_names[now.weekday()],
        "date": now.strftime("%B %d, %Y"),
        "is_weekend": now.weekday() >= 5,
        "day_type": _get_day_type(),
        "hint": "Use this to recommend currently open locations and appropriate meal periods."
    }

# Categories that are "build your own" stations - items are components, not complete meals
COMPONENT_CATEGORIES = {
    # Salad bars
    "fresh 52 salad bar", "salad bar", "salad bar toppings", "salad bar dressings",
    "salad bar protein", "salad bar greens", "salad bar fruit and yogurt",
    "global fruit & yogurt",
    # Deli/sandwich building
    "deli", "deli sauce", "deli veg", "deli cheese", "create deli", "ny deli",
    # Taqueria building
    "taqueria toppings", "taqueria base", "taqueria protein",
    # Build your own stations
    "innovate", "grill / flame", "grill", "create",
    "pom and honey choose your side", "pom and honey choose your protein",
    "pom and honey grain and salad", "pom and honey sauce",
    "street eats choose your side", "street eats choose your protein",
    "paper lantern sides", "paper lantern starch", "paper lantern protein",
    "culture corner starch", "culture corner side",
    # Misc components
    "root and seeds", "plant based", "plant'd",
}

# Categories that are complete entrees/meals
ENTREE_CATEGORIES = {
    "true burger", "burger 212", "burger 212 grill", "crave nyu",
    "cluckstein", "500 degrees pizza", "al forno pizza", "personal pizza",
    "pizza station", "pizza/alforno", "quesadilla/burrito/slider",
    "taqueria/tots/mac&cheese", "homestyle", "cucina entree", "cucina pasta",
    "halal station", "halal", "composed salad / sandwiches",
    "fresh 52 composed salads", "root and seeds composed", "breakfast sandwiches",
    "kimmel lunch", "kimmel dinner", "fresh 140", "fresh 140 sandwich",
    "vedgecraft", "waffle stein", "guacamole toast", "soup of the day",
    "the soup bowl", "soup bowl", "soup", "spoonfuls",
    # Palladium specific
    "culture corner entree", "paper lantern protein",
}


def _classify_item_type(category: str) -> str:
    """Classify an item as 'component', 'entree', or 'other' based on category"""
    cat_lower = category.lower() if category else ""

    if cat_lower in COMPONENT_CATEGORIES:
        return "component"
    elif cat_lower in ENTREE_CATEGORIES:
        return "entree"
    else:
        # Heuristic: if it has "choose your" or "bar" or "toppings", it's a component
        if any(x in cat_lower for x in ["choose your", "bar", "toppings", "sides", "sauce"]):
            return "component"
        return "other"


def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_current_date() -> str:
    """Get the most recent date in the database"""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(date) FROM menu_items")
    date = c.fetchone()[0]
    conn.close()
    return date


def list_locations() -> list[str]:
    """
    Get all available dining locations.

    Returns:
        List of location names
    """
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM locations ORDER BY name")
    locations = [row[0] for row in c.fetchall()]
    conn.close()
    return locations


def get_location_hours(location: str) -> dict:
    """
    Get operating hours for a dining location for TODAY.
    Automatically adjusts based on current day of the week.

    Args:
        location: Dining hall name (partial match supported)

    Returns:
        Dict with location name, today's hours, and current time context
    """
    now = datetime.now()
    day_type = _get_day_type()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Find matching location
    location_lower = location.lower()
    for loc_name, all_hours in DINING_HOURS.items():
        if location_lower in loc_name.lower():
            today_hours = all_hours.get(day_type)

            if today_hours is None:
                return {
                    "location": loc_name,
                    "today": day_names[now.weekday()],
                    "current_time": now.strftime("%I:%M %p"),
                    "hours": None,
                    "status": "CLOSED today",
                    "note": f"{loc_name} is closed on {day_names[now.weekday()]}s."
                }

            return {
                "location": loc_name,
                "today": day_names[now.weekday()],
                "current_time": now.strftime("%I:%M %p"),
                "hours": today_hours,
                "status": "Open today",
                "note": "Hours may vary on holidays. Check NYU Eats for updates."
            }

    return {
        "location": location,
        "today": day_names[now.weekday()],
        "current_time": now.strftime("%I:%M %p"),
        "hours": None,
        "status": "Unknown",
        "note": "Hours not available for this location."
    }


def get_all_hours() -> dict:
    """
    Get operating hours for all dining locations for TODAY.

    Returns:
        Dict with all locations and their hours for today
    """
    now = datetime.now()
    day_type = _get_day_type()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    today_hours = {}
    for loc_name, all_hours in DINING_HOURS.items():
        hours = all_hours.get(day_type)
        if hours:
            today_hours[loc_name] = {"status": "Open", "hours": hours}
        else:
            today_hours[loc_name] = {"status": "Closed"}

    return {
        "today": day_names[now.weekday()],
        "current_time": now.strftime("%I:%M %p"),
        "locations": today_hours,
        "note": "Hours may vary on holidays. Check NYU Eats for updates."
    }


def search_menu(
    keywords: Optional[list[str]] = None,
    period: Optional[str] = None,
    location: Optional[str] = None,
    dietary_tags: Optional[list[str]] = None,
    min_protein: Optional[float] = None,
    max_calories: Optional[int] = None,
    min_calories: Optional[int] = None,
    max_sodium: Optional[float] = None,
    min_fiber: Optional[float] = None,
    max_sugar: Optional[float] = None,
    limit: int = 20
) -> list[dict]:
    """
    Search menu items with flexible filters.

    Args:
        keywords: Words to search for in item names (e.g., ["chicken", "grilled"])
        period: Meal period - "Breakfast", "Lunch", or "Dinner"
        location: Specific dining hall name (e.g., "Palladium", "Third North")
        dietary_tags: Filter by dietary tags (e.g., ["Vegan", "Vegetarian", "Avoiding Gluten"])
        min_protein: Minimum protein in grams
        max_calories: Maximum calories
        min_calories: Minimum calories (for bulking)
        max_sodium: Maximum sodium in mg (for low-sodium diets)
        min_fiber: Minimum fiber in grams (for high-fiber needs)
        max_sugar: Maximum sugar in grams (for low-sugar diets)
        limit: Maximum number of results (default 20)

    Returns:
        List of matching menu items with full nutrition info
    """
    conn = _get_connection()
    c = conn.cursor()

    date = _get_current_date()

    # Build query dynamically
    query = """
        SELECT
            mi.name,
            l.name as location,
            mi.period,
            mi.category,
            mi.calories,
            mi.protein,
            mi.carbs,
            mi.fat,
            mi.fiber,
            mi.sugar,
            mi.sodium,
            mi.saturated_fat,
            mi.cholesterol,
            mi.dietary_tags
        FROM menu_items mi
        JOIN locations l ON mi.location_id = l.id
        WHERE mi.date = ?
    """
    params = [date]

    # Period filter (handle Dinner/Supper as equivalent)
    if period:
        if period.lower() == "dinner":
            query += " AND (LOWER(mi.period) = 'dinner' OR LOWER(mi.period) = 'supper')"
        else:
            query += " AND LOWER(mi.period) = LOWER(?)"
            params.append(period)

    # Location filter (partial match)
    if location:
        query += " AND LOWER(l.name) LIKE LOWER(?)"
        params.append(f"%{location}%")

    # Keyword search in item name
    if keywords:
        keyword_conditions = []
        for kw in keywords:
            keyword_conditions.append("LOWER(mi.name) LIKE LOWER(?)")
            params.append(f"%{kw}%")
        query += f" AND ({' OR '.join(keyword_conditions)})"

    # Dietary tag filter
    if dietary_tags:
        tag_conditions = []
        for tag in dietary_tags:
            tag_conditions.append("LOWER(mi.dietary_tags) LIKE LOWER(?)")
            params.append(f"%{tag}%")
        query += f" AND ({' AND '.join(tag_conditions)})"

    # Nutrition filters
    if min_protein is not None:
        query += " AND mi.protein >= ?"
        params.append(min_protein)

    if max_calories is not None:
        query += " AND mi.calories <= ?"
        params.append(max_calories)

    if min_calories is not None:
        query += " AND mi.calories >= ?"
        params.append(min_calories)

    if max_sodium is not None:
        query += " AND mi.sodium IS NOT NULL AND mi.sodium <= ?"
        params.append(max_sodium)

    if min_fiber is not None:
        query += " AND mi.fiber IS NOT NULL AND mi.fiber >= ?"
        params.append(min_fiber)

    if max_sugar is not None:
        query += " AND mi.sugar IS NOT NULL AND mi.sugar <= ?"
        params.append(max_sugar)

    # Order by protein (descending) for high-protein queries, else by name
    if min_protein:
        query += " ORDER BY mi.protein DESC"
    else:
        query += " ORDER BY mi.calories ASC"

    query += f" LIMIT {limit}"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    # Format results
    results = []
    seen = set()  # Deduplicate

    for row in rows:
        key = (row["name"], row["location"], row["period"])
        if key in seen:
            continue
        seen.add(key)

        item_type = _classify_item_type(row["category"])

        results.append({
            "name": row["name"],
            "location": row["location"],
            "period": row["period"],
            "category": row["category"],
            "item_type": item_type,  # "component", "entree", or "other"
            "calories": row["calories"],
            "protein": row["protein"],
            "carbs": row["carbs"],
            "fat": row["fat"],
            "fiber": row["fiber"],
            "sugar": row["sugar"],
            "sodium": row["sodium"],
            "saturated_fat": row["saturated_fat"],
            "cholesterol": row["cholesterol"],
            "dietary_tags": row["dietary_tags"].split(",") if row["dietary_tags"] else []
        })

    return results


def get_location_items(
    location: str,
    period: Optional[str] = None,
    limit: int = 40
) -> list[dict]:
    """
    Get all menu items from a specific dining location.
    Useful for building complete meal combinations from one place.

    Args:
        location: Dining hall name (e.g., "Palladium", "Third North")
        period: Optional meal period filter
        limit: Maximum items to return

    Returns:
        List of all items at that location
    """
    return search_menu(
        location=location,
        period=period,
        limit=limit
    )


def get_high_protein_items(
    min_protein: float = 15,
    location: Optional[str] = None,
    period: Optional[str] = None,
    limit: int = 15
) -> list[dict]:
    """
    Get items with high protein content.

    Args:
        min_protein: Minimum protein in grams (default 15g)
        location: Optional location filter
        period: Optional meal period filter
        limit: Maximum results

    Returns:
        List of high-protein items sorted by protein content
    """
    return search_menu(
        min_protein=min_protein,
        location=location,
        period=period,
        limit=limit
    )


def get_complete_meals(
    location: Optional[str] = None,
    period: Optional[str] = None,
    dietary_tags: Optional[list[str]] = None,
    min_protein: Optional[float] = None,
    max_calories: Optional[int] = None,
    min_calories: int = 250,  # Minimum calories for a "real" meal
    max_sodium: Optional[float] = None,
    min_fiber: Optional[float] = None,
    max_sugar: Optional[float] = None,
    limit: int = 15
) -> list[dict]:
    """
    Get COMPLETE MEALS (entrees, sandwiches, burgers, etc.) - NOT components.
    Use this when the user wants a ready-to-eat item, not build-your-own.
    Only returns items with at least 250 calories (real meals, not sides).

    Args:
        location: Optional dining hall filter
        period: Optional meal period
        dietary_tags: Optional dietary restrictions
        min_protein: Minimum protein
        max_calories: Maximum calories
        min_calories: Minimum calories (default 250) - filters out small sides
        max_sodium: Maximum sodium in mg
        min_fiber: Minimum fiber in grams
        max_sugar: Maximum sugar in grams
        limit: Max results

    Returns:
        List of complete meal items (entrees, not components) with 250+ calories
    """
    all_items = search_menu(
        location=location,
        period=period,
        dietary_tags=dietary_tags,
        min_protein=min_protein,
        max_calories=max_calories,
        min_calories=min_calories,  # Enforce minimum
        max_sodium=max_sodium,
        min_fiber=min_fiber,
        max_sugar=max_sugar,
        limit=limit * 3  # Get more to filter
    )

    # Filter to only entrees with sufficient calories
    entrees = [
        item for item in all_items
        if item.get("item_type") == "entree"
        and item.get("calories") and item["calories"] >= min_calories
    ]

    return entrees[:limit]


def get_build_your_own_options(
    location: str,
    station_type: Optional[str] = None,
    period: Optional[str] = None,
    dietary_tags: Optional[list[str]] = None,
    limit: int = 25
) -> dict:
    """
    Get components for building your own meal at a station (salad bar, deli, taco bar, etc.)
    Returns items grouped by type (proteins, bases, toppings, sauces).

    Args:
        location: Dining hall name
        station_type: Type of station - "salad", "deli", "taco", "bowl" (optional)
        period: Meal period
        dietary_tags: Dietary restrictions
        limit: Max items per category

    Returns:
        Dict with categorized components for building a meal
    """
    all_items = search_menu(
        location=location,
        period=period,
        dietary_tags=dietary_tags,
        limit=100
    )

    # Filter to components only
    components = [item for item in all_items if item.get("item_type") == "component"]

    # Categorize by likely role in a meal
    proteins = []
    bases = []
    toppings = []
    sauces = []
    other = []

    protein_keywords = ["chicken", "beef", "turkey", "tuna", "salmon", "tofu", "egg", "ham", "bacon", "sausage"]
    base_keywords = ["rice", "quinoa", "bread", "tortilla", "pasta", "noodle", "lettuce", "greens", "wrap", "bun", "roll"]
    sauce_keywords = ["sauce", "dressing", "mayo", "mustard", "vinegar", "oil", "guac", "salsa", "hummus"]

    for item in components:
        name_lower = item["name"].lower()
        cat_lower = (item.get("category") or "").lower()

        if any(kw in name_lower for kw in protein_keywords) or item.get("protein", 0) and item["protein"] >= 8:
            proteins.append(item)
        elif any(kw in name_lower for kw in base_keywords):
            bases.append(item)
        elif any(kw in name_lower or kw in cat_lower for kw in sauce_keywords):
            sauces.append(item)
        else:
            toppings.append(item)

    return {
        "location": location,
        "proteins": proteins[:limit],
        "bases": bases[:limit],
        "toppings": toppings[:limit],
        "sauces": sauces[:limit],
        "build_suggestion": f"At {location}, you can build your own meal by choosing a base, protein, toppings, and sauce."
    }


def get_low_calorie_items(
    max_calories: int = 400,
    location: Optional[str] = None,
    period: Optional[str] = None,
    dietary_tags: Optional[list[str]] = None,
    limit: int = 15
) -> list[dict]:
    """
    Get low-calorie menu items.

    Args:
        max_calories: Maximum calories (default 400)
        location: Optional location filter
        period: Optional meal period filter
        dietary_tags: Optional dietary restrictions
        limit: Maximum results

    Returns:
        List of low-calorie items sorted by calories
    """
    return search_menu(
        max_calories=max_calories,
        location=location,
        period=period,
        dietary_tags=dietary_tags,
        limit=limit
    )


# Tool definitions for OpenAI function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_complete_meals",
            "description": "Get COMPLETE ready-to-eat meals (burgers, sandwiches, pizzas, entrees). Use this FIRST when user wants a meal recommendation. These are NOT components - they are full dishes. Now includes detailed nutrition data (fiber, sugar, sodium, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Dining hall name (e.g., 'Palladium', 'Third North')"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["Breakfast", "Lunch", "Dinner"],
                        "description": "Meal period"
                    },
                    "dietary_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dietary restrictions: 'Vegan', 'Vegetarian', 'Avoiding Gluten'"
                    },
                    "min_protein": {
                        "type": "number",
                        "description": "Minimum protein in grams"
                    },
                    "max_calories": {
                        "type": "integer",
                        "description": "Maximum calories"
                    },
                    "max_sodium": {
                        "type": "number",
                        "description": "Maximum sodium in mg (for low-sodium diets)"
                    },
                    "min_fiber": {
                        "type": "number",
                        "description": "Minimum fiber in grams (for high-fiber needs)"
                    },
                    "max_sugar": {
                        "type": "number",
                        "description": "Maximum sugar in grams (for diabetic/low-sugar needs)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_build_your_own_options",
            "description": "Get components for BUILD-YOUR-OWN stations (salad bar, deli, taco bar). Returns proteins, bases, toppings, and sauces separately. Use when user wants to customize or build their own meal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Dining hall name"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["Breakfast", "Lunch", "Dinner"],
                        "description": "Meal period"
                    },
                    "dietary_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dietary restrictions"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_menu",
            "description": "General search for menu items with advanced nutrition filters. Use get_complete_meals for ready-to-eat dishes, or get_build_your_own_options for customizable stations. Use this for specific keyword searches or advanced nutrition filtering (fiber, sodium, sugar).",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Words to search for (e.g., ['pizza'], ['chicken'])"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["Breakfast", "Lunch", "Dinner"],
                        "description": "Meal period"
                    },
                    "location": {
                        "type": "string",
                        "description": "Dining hall name"
                    },
                    "dietary_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dietary restrictions"
                    },
                    "min_protein": {
                        "type": "number",
                        "description": "Minimum protein in grams"
                    },
                    "max_calories": {
                        "type": "integer",
                        "description": "Maximum calories"
                    },
                    "max_sodium": {
                        "type": "number",
                        "description": "Maximum sodium in mg (for low-sodium diets, recommended <600mg per meal)"
                    },
                    "min_fiber": {
                        "type": "number",
                        "description": "Minimum fiber in grams (for high-fiber needs, 5g+ is good)"
                    },
                    "max_sugar": {
                        "type": "number",
                        "description": "Maximum sugar in grams (for low-sugar/diabetic needs)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_locations",
            "description": "Get all NYU dining locations.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_location_hours",
            "description": "Get operating hours for a specific dining location for TODAY. Returns hours based on current day of week (weekday/weekend) and tells you if the location is open or closed today.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Dining hall name (e.g., 'Third North', 'Kimmel', 'Palladium')"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time, day of week, and date. Use this at the START of every request to know what meal period it is (breakfast/lunch/dinner) and whether it's a weekday or weekend.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# Map function names to actual functions
TOOL_FUNCTIONS = {
    "search_menu": search_menu,
    "get_location_items": get_location_items,
    "list_locations": list_locations,
    "get_complete_meals": get_complete_meals,
    "get_build_your_own_options": get_build_your_own_options,
    "get_high_protein_items": get_high_protein_items,
    "get_low_calorie_items": get_low_calorie_items,
    "get_location_hours": get_location_hours,
    "get_current_time": get_current_time,
}


if __name__ == "__main__":
    # Test the tools
    print("Testing search_menu for high protein lunch:")
    results = search_menu(min_protein=20, period="Lunch", limit=5)
    for r in results:
        print(f"  {r['name']} @ {r['location']} - {r['protein']}g protein, {r['calories']} cal")

    print("\nTesting vegan search:")
    results = search_menu(dietary_tags=["Vegan"], period="Lunch", limit=5)
    for r in results:
        print(f"  {r['name']} @ {r['location']} - {r['dietary_tags']}")

    print("\nTesting location items:")
    results = get_location_items("Palladium", period="Lunch", limit=5)
    for r in results:
        print(f"  {r['name']} - {r['calories']} cal")
