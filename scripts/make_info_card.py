from pathlib import Path
import html

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"

NOW = "Learning AI/ML • Exploring AI Engineer roles • Exploring LLMs & RAG"
PREV = "Freelancing • Built 3–4 projects for real clients"
STACK = "Python • Java • React • HTML • CSS • Node.js • Tailwind CSS • Git • Docker"
HIGHLIGHTS = "AI/ML • LLMs • RAG • Real-world client projects"


def esc(text):
    return html.escape(text)


lines = [
    ("Now", NOW),
    ("Prev", PREV),
    ("Stack", STACK),
    ("Highlights", HIGHLIGHTS),
]

width = 900
height = 360

svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}">

  <rect width="100%" height="100%" rx="14"
        fill="#0d1117"
        stroke="#30363d"/>

  <!-- Terminal title bar -->
  <rect width="100%" height="48"
        rx="14"
        fill="#161b22"/>

  <circle cx="22" cy="24" r="6" fill="#ff5f56"/>
  <circle cx="42" cy="24" r="6" fill="#ffbd2e"/>
  <circle cx="62" cy="24" r="6" fill="#27c93f"/>

  <text x="90" y="30"
        fill="#8b949e"
        font-family="monospace"
        font-size="15">
    avi@github ~ $ whoami
  </text>

'''

y = 92

for index, (key, value) in enumerate(lines):
    delay = index * 0.25

    svg += f'''
  <text x="38" y="{y}"
        fill="#58a6ff"
        font-family="monospace"
        font-size="17"
        font-weight="bold"
        opacity="0">
    {esc(key)}:
    <animate attributeName="opacity"
             from="0" to="1"
             begin="{delay}s"
             dur="0.5s"
             fill="freeze"/>
  </text>

  <text x="180" y="{y}"
        fill="#c9d1d9"
        font-family="monospace"
        font-size="16"
        opacity="0">
    {esc(value)}
    <animate attributeName="opacity"
             from="0" to="1"
             begin="{delay}s"
             dur="0.5s"
             fill="freeze"/>
  </text>
'''

    y += 62

svg += '''
</svg>
'''

OUT.write_text(svg, encoding="utf-8")

print(f"Created: {OUT}")