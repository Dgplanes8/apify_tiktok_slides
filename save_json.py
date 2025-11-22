#!/usr/bin/env python3
import json
import sys

# Read JSON from the user's message and save it
# This is a workaround for very large JSON data

data_str = sys.stdin.read()
data = json.loads(data_str)

with open('tiktok_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Saved {len(data)} entries to tiktok_data.json")
