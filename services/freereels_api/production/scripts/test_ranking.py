#!/usr/bin/env python3
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from freereels_client import FreeReelsClient

client = FreeReelsClient()
client.login_anonymous()

print("\n--- Verifying POST /frv2-api/homepage/v2/rank with {'key': ...} ---\n")

keys = ["daily", "weekly", "monthly", "annually"]

for k in keys:
    payload = {"key": k}
    resp = client._request("POST", "/frv2-api/homepage/v2/rank", json=payload)
    if resp and "items" in resp:
        items = resp["items"]
        print(f"[{k.upper()}] Total: {len(items)}")
        if items:
            print(f"  #1: {items[0].get('title')} (key: {items[0].get('key')})")
            if len(items) > 1:
                print(f"  #2: {items[1].get('title')}")
    else:
        print(f"[{k.upper()}] Response: {resp}")
    print()

print("\n--- Checking pagination support on /homepage/v2/rank ---")
# Check if page_info exists or pagination parameters work
payload_page2 = {"key": "daily", "page": 2, "offset": 10}
resp_p2 = client._request("POST", "/frv2-api/homepage/v2/rank", json=payload_page2)
if resp_p2:
    print("Keys in response:", list(resp_p2.keys()))
    print("page_info:", resp_p2.get("page_info"))
    print("has_more:", resp_p2.get("has_more"))
    if "items" in resp_p2 and resp_p2["items"]:
        print(f"Page 2 #1: {resp_p2['items'][0].get('title')}")
