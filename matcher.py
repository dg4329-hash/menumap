"""
MenuMap - AI Matching Engine
Takes natural language prompts and finds matching menu items
"""
import sqlite3
import re
from pathlib import Path
from dataclasses import dataclass

DB_PATH = Path(__file__).parent / "menumap.db"


@dataclass
class MatchResult:
    """A matched menu item with relevance score"""
    name: str
    location: str
    period: str
    category: str
    calories: int | None
    protein: float | None
    carbs: float | None
    fat: float | None
    dietary_tags: list[str]
    score: float
    match_reasons: list[str]


class MenuMatcher:
    """
    Matches user prompts to menu items using keyword and filter-based matching.
    For MVP, uses rule-based matching. Can be upgraded to embeddings/LLM later.
    """

    # Keyword mappings for common food cravings
    FOOD_KEYWORDS = {
        "pizza": ["pizza", "flatbread", "margherita"],
        "burger": ["burger", "hamburger", "cheeseburger"],
        "chicken": ["chicken", "poultry", "wings", "tenders", "grilled chicken"],
        "salad": ["salad", "greens", "lettuce", "spinach"],
        "pasta": ["pasta", "spaghetti", "penne", "linguine", "mac and cheese", "macaroni"],
        "sandwich": ["sandwich", "sub", "wrap", "panini", "hoagie"],
        "breakfast": ["eggs", "bacon", "pancakes", "waffle", "oatmeal", "cereal", "toast"],
        "coffee": ["coffee", "latte", "espresso", "cappuccino", "mocha"],
        "smoothie": ["smoothie", "shake", "blend"],
        "soup": ["soup", "chili", "stew", "broth"],
        "asian": ["stir fry", "rice bowl", "teriyaki", "lo mein", "fried rice", "sushi", "ramen"],
        "mexican": ["taco", "burrito", "quesadilla", "nachos", "guac"],
        "healthy": ["grilled", "steamed", "fresh", "salad", "lean"],
        "comfort": ["mac and cheese", "mashed", "gravy", "fried", "crispy"],
        "sweet": ["dessert", "cookie", "cake", "ice cream", "brownie", "muffin"],
        "fruit": ["fruit", "apple", "banana", "orange", "berry", "melon"],
        "protein": ["chicken", "beef", "steak", "fish", "salmon", "tuna", "tofu", "eggs"],
    }

    # Dietary restriction patterns
    DIETARY_PATTERNS = {
        "vegan": "Vegan",
        "vegetarian": "Vegetarian",
        "gluten-free": "Avoiding Gluten",
        "gluten free": "Avoiding Gluten",
        "no gluten": "Avoiding Gluten",
        "halal": "Halal",
        "kosher": "Kosher",
    }

    # Nutritional goal patterns
    NUTRITION_PATTERNS = {
        r"high protein|protein rich|lots of protein": {"protein": (">=", 20)},
        r"low calorie|light|diet|under (\d+) cal": {"calories": ("<=", 400)},
        r"low carb|keto": {"carbs": ("<=", 20)},
        r"low fat": {"fat": ("<=", 10)},
        r"high calorie|bulking|gains": {"calories": (">=", 600)},
    }

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _parse_prompt(self, prompt: str) -> dict:
        """Parse user prompt into structured query parameters"""
        prompt_lower = prompt.lower()

        parsed = {
            "food_keywords": [],
            "dietary_filters": [],
            "nutrition_filters": {},
            "period": None,
            "location_preference": None,
        }

        # Extract food keywords
        for category, keywords in self.FOOD_KEYWORDS.items():
            for kw in keywords:
                if kw in prompt_lower:
                    parsed["food_keywords"].append(kw)

        # Extract dietary restrictions
        for pattern, tag in self.DIETARY_PATTERNS.items():
            if pattern in prompt_lower:
                parsed["dietary_filters"].append(tag)

        # Extract meal period
        if "breakfast" in prompt_lower:
            parsed["period"] = "Breakfast"
        elif "lunch" in prompt_lower:
            parsed["period"] = "Lunch"
        elif "dinner" in prompt_lower:
            parsed["period"] = "Dinner"

        # Extract nutritional goals
        for pattern, filters in self.NUTRITION_PATTERNS.items():
            if re.search(pattern, prompt_lower):
                parsed["nutrition_filters"].update(filters)

        # Extract specific calorie limit
        cal_match = re.search(r"under (\d+)\s*(?:cal|calories)", prompt_lower)
        if cal_match:
            parsed["nutrition_filters"]["calories"] = ("<=", int(cal_match.group(1)))

        # Extract protein target
        protein_match = re.search(r"(\d+)\s*(?:g|grams?)?\s*(?:of\s*)?protein", prompt_lower)
        if protein_match:
            parsed["nutrition_filters"]["protein"] = (">=", int(protein_match.group(1)))

        return parsed

    def _score_item(self, item: dict, parsed: dict) -> tuple[float, list[str]]:
        """Calculate match score and reasons for a menu item"""
        score = 0.0
        reasons = []

        item_name_lower = item["name"].lower()
        item_desc_lower = (item.get("description") or "").lower()
        item_tags = (item.get("dietary_tags") or "").split(",")

        # Food keyword matching (0-40 points)
        for kw in parsed["food_keywords"]:
            if kw in item_name_lower or kw in item_desc_lower:
                score += 20
                reasons.append(f"matches '{kw}'")

        # Dietary filter matching (0-30 points)
        for diet_tag in parsed["dietary_filters"]:
            if diet_tag in item_tags:
                score += 30
                reasons.append(diet_tag)

        # Period matching (0-10 points)
        if parsed["period"] and item.get("period") == parsed["period"]:
            score += 10
            reasons.append(f"{parsed['period']} item")

        # Nutritional goals (0-20 points)
        for nutrient, (op, target) in parsed.get("nutrition_filters", {}).items():
            value = item.get(nutrient)
            if value is not None:
                if op == ">=" and value >= target:
                    score += 20
                    reasons.append(f"{nutrient}: {value}")
                elif op == "<=" and value <= target:
                    score += 20
                    reasons.append(f"{nutrient}: {value}")

        return score, reasons

    def search(self, prompt: str, limit: int = 10, date: str = None) -> list[MatchResult]:
        """
        Search for menu items matching the user's prompt.

        Args:
            prompt: Natural language query (e.g., "high protein lunch under 500 calories")
            limit: Maximum number of results to return
            date: Date to search (defaults to most recent)

        Returns:
            List of MatchResult objects sorted by relevance
        """
        parsed = self._parse_prompt(prompt)

        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Get the date to search
        if date is None:
            c.execute("SELECT MAX(date) FROM menu_items")
            date = c.fetchone()[0]

        # Build query
        query = '''
            SELECT
                mi.name, mi.period, mi.category, mi.description,
                mi.calories, mi.protein, mi.carbs, mi.fat,
                mi.dietary_tags, mi.allergens,
                l.name as location_name
            FROM menu_items mi
            JOIN locations l ON mi.location_id = l.id
            WHERE mi.date = ?
        '''
        params = [date]

        # Add period filter if specified
        if parsed["period"]:
            query += " AND mi.period = ?"
            params.append(parsed["period"])

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        # Score and rank results
        results = []
        for row in rows:
            item = dict(row)
            score, reasons = self._score_item(item, parsed)

            if score > 0:  # Only include items with some match
                results.append(MatchResult(
                    name=item["name"],
                    location=item["location_name"],
                    period=item["period"],
                    category=item["category"],
                    calories=item["calories"],
                    protein=item["protein"],
                    carbs=item["carbs"],
                    fat=item["fat"],
                    dietary_tags=item["dietary_tags"].split(",") if item["dietary_tags"] else [],
                    score=score,
                    match_reasons=reasons
                ))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:limit]

    def get_locations(self) -> list[str]:
        """Get all available dining locations"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM locations ORDER BY name")
        locations = [row[0] for row in c.fetchall()]
        conn.close()
        return locations

    def get_stats(self, date: str = None) -> dict:
        """Get statistics about available menu items"""
        conn = self._get_connection()
        c = conn.cursor()

        if date is None:
            c.execute("SELECT MAX(date) FROM menu_items")
            date = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM menu_items WHERE date = ?", (date,))
        total_items = c.fetchone()[0]

        c.execute("""
            SELECT l.name, COUNT(*) as count
            FROM menu_items mi
            JOIN locations l ON mi.location_id = l.id
            WHERE mi.date = ?
            GROUP BY l.name
            ORDER BY count DESC
        """, (date,))
        by_location = {row[0]: row[1] for row in c.fetchall()}

        conn.close()

        return {
            "date": date,
            "total_items": total_items,
            "by_location": by_location
        }


def demo():
    """Demo the matching engine"""
    matcher = MenuMatcher()

    print("=" * 60)
    print("MenuMap - AI Matching Demo")
    print("=" * 60)

    # Show stats
    stats = matcher.get_stats()
    print(f"\nMenu data for: {stats['date']}")
    print(f"Total items: {stats['total_items']}")

    # Test queries
    test_queries = [
        "high protein lunch",
        "vegan breakfast",
        "pizza",
        "something healthy under 400 calories",
        "coffee",
        "gluten free dinner",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: \"{query}\"")
        print("-" * 60)

        results = matcher.search(query, limit=5)

        if not results:
            print("  No matches found")
        else:
            for i, r in enumerate(results, 1):
                tags = ", ".join(r.dietary_tags[:3]) if r.dietary_tags else "none"
                print(f"  {i}. {r.name}")
                print(f"     @ {r.location} ({r.period})")
                print(f"     {r.calories or '?'} cal | {r.protein or '?'}g protein | Tags: {tags}")
                print(f"     Matched: {', '.join(r.match_reasons)}")


if __name__ == "__main__":
    demo()
