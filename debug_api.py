"""
Debug the dineoncampus API response
"""
import requests

API_URL = "https://api.dineoncampus.com/v1/"

# Test different endpoints
endpoints = [
    "sites/NYUeats/info",
    "sites/public",
]

for endpoint in endpoints:
    url = API_URL + endpoint
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print('='*60)

    resp = requests.get(url)
    print(f"Status: {resp.status_code}")
    print(f"Headers: {dict(resp.headers)[:200] if resp.headers else 'None'}")
    print(f"Content (first 500 chars): {resp.text[:500]}")
