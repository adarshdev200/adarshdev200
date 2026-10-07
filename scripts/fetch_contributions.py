import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


USERNAME = "adarshdev200"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

days = []

for rect in soup.select("td.ContributionCalendar-day"):
    date = rect.get("data-date")
    level = rect.get("data-level")

    if date and level:
        days.append({
            "date": date,
            "level": int(level)
        })

data = {
    "username": USERNAME,
    "days": days
}

OUT.parent.mkdir(parents=True, exist_ok=True)

OUT.write_text(
    json.dumps(data, indent=2),
    encoding="utf-8"
)

print(f"Saved {len(days)} contribution days to {OUT}")