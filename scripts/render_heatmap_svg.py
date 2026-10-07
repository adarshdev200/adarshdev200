import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

data = json.loads(DATA.read_text(encoding="utf-8"))

days = data["days"]

# GitHub contribution colors
COLORS = [
    "#161b22",
    "#0e4429",
    "#006d32",
    "#26a641",
    "#39d353",
    "#69f0a0",
]

# Graph dimensions
CELL = 12
GAP = 4

LEFT = 40
TOP = 35

WIDTH = 860
HEIGHT = 190

svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}">

  <rect width="100%" height="100%"
        rx="14"
        fill="#0d1117"
        stroke="#30363d"/>

  <text x="40" y="24"
        fill="#8b949e"
        font-family="monospace"
        font-size="12">
    CONTRIBUTIONS
  </text>
'''

# Draw contribution cells
for i, day in enumerate(days):

    try:
        d = date.fromisoformat(day["date"])
    except ValueError:
        continue

    level = max(0, min(5, int(day["level"])))

    # Monday = 0 ... Sunday = 6
    weekday = d.weekday()

    # Week number relative to first day
    first_date = date.fromisoformat(days[0]["date"])
    week = (d - first_date).days // 7

    x = LEFT + week * (CELL + GAP)
    y = TOP + weekday * (CELL + GAP)

    delay = i * 0.008

    svg += f'''
  <rect
      x="{x}"
      y="{y}"
      width="{CELL}"
      height="{CELL}"
      rx="2"
      fill="{COLORS[level]}"
      opacity="0">

    <animate
        attributeName="opacity"
        from="0"
        to="1"
        begin="{delay:.3f}s"
        dur="0.3s"
        fill="freeze"/>
  </rect>
'''

# Legend
legend_y = 150

svg += f'''
  <text x="40" y="{legend_y}"
        fill="#8b949e"
        font-family="monospace"
        font-size="11">
    Less
  </text>
'''

for i, color in enumerate(COLORS):

    x = 75 + i * 18

    svg += f'''
  <rect
      x="{x}"
      y="{legend_y - 10}"
      width="12"
      height="12"
      rx="2"
      fill="{color}"/>
'''

svg += f'''
  <text x="190" y="{legend_y}"
        fill="#8b949e"
        font-family="monospace"
        font-size="11">
    More
  </text>

</svg>
'''

OUT.write_text(svg, encoding="utf-8")

print(f"Created: {OUT}")