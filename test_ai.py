"""
Test script for MenuMap AI Coach
Run with: OPENAI_API_KEY=your_key python3 test_ai.py
"""
from ai_coach import get_recommendation
import time

TEST_QUERIES = [
    # Test 1: High protein pasta (should build a complete meal)
    "pasta, high protein under 1000 calories above 60g of protein",

    # Test 2: Simple pasta (should still build complete meal)
    "I want pasta for dinner",

    # Test 3: Rice bowl (another base item test)
    "high protein rice bowl",

    # Test 4: Complete meal query (should find entrees)
    "burger with lots of protein",

    # Test 5: Vegan with specific requirements
    "vegan high protein lunch",

    # Test 6: Low calorie but filling
    "something under 400 calories but filling",
]

def run_tests():
    print("=" * 70)
    print("MenuMap AI Coach - Test Suite")
    print("=" * 70)

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}: {query}")
        print("-" * 70)

        try:
            start = time.time()
            response = get_recommendation(query)
            elapsed = time.time() - start

            print(response)
            print(f"\n[Response time: {elapsed:.1f}s]")

        except Exception as e:
            print(f"ERROR: {e}")

        print()
        time.sleep(1)  # Rate limiting


if __name__ == "__main__":
    run_tests()
