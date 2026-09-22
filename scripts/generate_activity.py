import os
import json
import urllib.request
import datetime
import html


USERNAME = os.environ.get("GITHUB_USERNAME", "ArfaMunam47")
TOKEN = os.environ.get("GITHUB_TOKEN")

OUTPUT = "activity-trail.svg"


# ============================================================
# GITHUB GRAPHQL
# ============================================================

today = datetime.datetime.now(
    datetime.timezone.utc
).replace(
    hour=23,
    minute=59,
    second=59,
    microsecond=0
)

start = today - datetime.timedelta(days=181)


query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {

    createdAt

    contributionsCollection(
      from: $from
      to: $to
    ) {
      contributionCalendar {
        totalContributions

        weeks {
          contributionDays {
            date
            contributionCount
            weekday
          }
        }
      }
    }

    repositories(
      first: 100
      ownerAffiliations: OWNER
      privacy: PUBLIC
    ) {
      totalCount

      nodes {
        stargazerCount
      }
    }
  }
}
"""


variables = {
    "login": USERNAME,
    "from": start.isoformat().replace("+00:00", "Z"),
    "to": today.isoformat().replace("+00:00", "Z")
}


payload = json.dumps({
    "query": query,
    "variables": variables
}).encode("utf-8")


request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "activity-trail-generator"
    }
)


with urllib.request.urlopen(request) as response:
    result = json.loads(response.read().decode())


if "errors" in result:
    raise RuntimeError(
        json.dumps(result["errors"], indent=2)
    )


user = result["data"]["user"]

calendar = user[
    "contributionsCollection"
]["contributionCalendar"]


weeks = calendar["weeks"]


# ============================================================
# CONTRIBUTION DATA
# ============================================================

days = []

for week in weeks:
    for day in week["contributionDays"]:
        days.append(day)


# Make sure we have exactly the latest 26 weeks.
days = days[-182:]


# Group into weeks
weeks_data = []

for i in range(0, len(days), 7):
    weeks_data.append(days[i:i + 7])


# ============================================================
# STATS
# ============================================================

total_contributions = calendar["totalContributions"]

public_repos = user["repositories"]["totalCount"]

total_stars = sum(
    repo["stargazerCount"]
    for repo in user["repositories"]["nodes"]
)


created_at = datetime.datetime.fromisoformat(
    user["createdAt"].replace("Z", "+00:00")
)

now = datetime.datetime.now(datetime.timezone.utc)

months_active = (
    (now.year - created_at.year) * 12
    + now.month
    - created_at.month
)

months_active = max(1, months_active)


# ============================================================
# SVG HELPERS
# ============================================================

def esc(value):
    return html.escape(str(value))


def text(
    value,
    x,
    y,
    size=16,
    fill="#F2DCE5",
    weight="400",
    anchor="start"
):
    return f"""
    <text
        x="{x}"
        y="{y}"
        font-family="Inter, Arial, sans-serif"
        font-size="{size}"
        font-weight="{weight}"
        fill="{fill}"
        text-anchor="{anchor}"
    >{esc(value)}</text>
    """


def polygon(points, fill, stroke="#130B12"):
    points_string = " ".join(
        f"{x},{y}" for x, y in points
    )

    return f"""
    <polygon
        points="{points_string}"
        fill="{fill}"
        stroke="{stroke}"
        stroke-width="0.8"
    />
    """


# ============================================================
# COLORS
# ============================================================

BACKGROUND = "#08090D"
CARD = "#0C0A10"

PINK_0 = "#21131D"
PINK_1 = "#4A1D34"
PINK_2 = "#742A4C"
PINK_3 = "#A83B68"
PINK_4 = "#D95382"
PINK_5 = "#F47EAA"

GRID = [
    PINK_0,
    PINK_1,
    PINK_2,
    PINK_3,
    PINK_4,
    PINK_5
]


# ============================================================
# CONTRIBUTION LEVEL
# ============================================================

max_count = max(
    [d["contributionCount"] for d in days] or [1]
)


def level(count):

    if count <= 0:
        return 0

    ratio = count / max_count

    if ratio < 0.15:
        return 1

    if ratio < 0.35:
        return 2

    if ratio < 0.55:
        return 3

    if ratio < 0.75:
        return 4

    return 5


# ============================================================
# SVG DOCUMENT
# ============================================================

WIDTH = 1500
HEIGHT = 950

svg = f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>

<defs>

    <filter
        id="pinkGlow"
        x="-100%"
        y="-100%"
        width="300%"
        height="300%"
    >
        <feGaussianBlur
            stdDeviation="7"
            result="blur"
        />

        <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
        </feMerge>
    </filter>

    <linearGradient
        id="pinkGradient"
        x1="0"
        y1="0"
        x2="1"
        y2="1"
    >
        <stop
            offset="0%"
            stop-color="#F47EAA"
        />

        <stop
            offset="100%"
            stop-color="#A83B68"
        />
    </linearGradient>

</defs>


<!-- =====================================================
     BACKGROUND
     ===================================================== -->

<rect
    width="{WIDTH}"
    height="{HEIGHT}"
    rx="24"
    fill="{BACKGROUND}"
/>


<!-- =====================================================
     OUTER CARD
     ===================================================== -->

<rect
    x="18"
    y="18"
    width="{WIDTH - 36}"
    height="{HEIGHT - 36}"
    rx="20"
    fill="none"
    stroke="#71324F"
    stroke-width="1.5"
/>


<!-- =====================================================
     ACTIVITY AREA
     ===================================================== -->

<rect
    x="55"
    y="55"
    width="1390"
    height="540"
    rx="18"
    fill="#050509"
    stroke="#54213B"
    stroke-width="1.2"
/>
"""


# ============================================================
# ISOMETRIC GRID
# ============================================================

# Position of the 3D calendar.
# Compact, centered layout: the calendar stays comfortably inside
# the activity panel and leaves a dedicated area for the month labels.
origin_x = 420
origin_y = 125

# Smaller cells keep the full 6-month trail compact and leave
# dedicated breathing room for weekday/month labels.
cell_x = 39
cell_y = 9

cube_height = 10

columns = min(26, len(weeks_data))


# We render from back to front so the stacks overlap naturally.
for col in range(columns):

    week = weeks_data[col]

    for row in range(min(7, len(week))):

        day = week[row]

        count = day["contributionCount"]
        lvl = level(count)

        base_x = (
            origin_x
            + col * cell_x
            - row * cell_x
        )

        base_y = (
            origin_y
            + col * cell_y
            + row * cell_y
        )

        # ----------------------------------------------------
        # Base diamond
        # ----------------------------------------------------

        top = (
            base_x,
            base_y
        )

        right = (
            base_x + cell_x / 2,
            base_y + cell_y
        )

        bottom = (
            base_x,
            base_y + cell_y * 2
        )

        left = (
            base_x - cell_x / 2,
            base_y + cell_y
        )

        svg += polygon(
            [
                top,
                right,
                bottom,
                left
            ],
            GRID[0]
        )


        # ----------------------------------------------------
        # Cube height
        # ----------------------------------------------------

        if count <= 0:
            continue


        height = cube_height * min(
            5,
            max(1, round(count / max_count * 6))
        )


        # Cube top
        cube_top = [
            (top[0], top[1] - height),
            (right[0], right[1] - height),
            (bottom[0], bottom[1] - height),
            (left[0], left[1] - height)
        ]


        # Glow only on strong activity
        glow = ""

        if lvl >= 4:
            glow = 'filter="url(#pinkGlow)"'


        # Top
        svg += f"""
        <polygon
            points="
                {cube_top[0][0]},{cube_top[0][1]}
                {cube_top[1][0]},{cube_top[1][1]}
                {cube_top[2][0]},{cube_top[2][1]}
                {cube_top[3][0]},{cube_top[3][1]}
            "
            fill="{GRID[lvl]}"
            {glow}
        />
        """


        # Left side
        svg += polygon(
            [
                cube_top[3],
                cube_top[2],
                bottom,
                left
            ],
            GRID[max(1, lvl - 1)]
        )


        # Right side
        svg += polygon(
            [
                cube_top[1],
                cube_top[2],
                bottom,
                right
            ],
            GRID[lvl]
        )


# ============================================================
# WEEKDAY LABELS
# ============================================================

svg += text(
    "Mon",
    90,
    165,
    15,
    "#E9C6D6",
    "500"
)

svg += text(
    "Wed",
    90,
    200,
    15,
    "#E9C6D6",
    "500"
)

svg += text(
    "Fri",
    90,
    235,
    15,
    "#E9C6D6",
    "500"
)


# ============================================================
# MONTH LABELS
# ============================================================

# Dedicated label row below the 3D calendar.
# Keeping these outside the grid prevents labels from colliding
# with cubes or the statistics cards.

month_positions = [
    ("MAR '26", 420),
    ("APR '26", 576),
    ("MAY '26", 732),
    ("JUN '26", 888),
    ("JUL '26", 1044),
    ("AUG '26", 1200),
    ("SEP '26", 1356)
]

for label, x in month_positions:
    svg += text(
        label,
        x,
        515,
        14,
        "#E875A0",
        "600",
        "middle"
    )


# ============================================================
# LEGEND
# ============================================================

legend_x = 90
legend_y = 640

svg += f"""
<rect
    x="{legend_x}"
    y="{legend_y}"
    width="400"
    height="80"
    rx="14"
    fill="#0B080E"
    stroke="#59213E"
/>
"""

svg += text(
    "LESS",
    legend_x + 22,
    legend_y + 47,
    15,
    "#E875A0",
    "700"
)


for i, color in enumerate(GRID):

    x = legend_x + 105 + i * 42

    svg += f"""
    <rect
        x="{x}"
        y="{legend_y + 27}"
        width="25"
        height="25"
        rx="4"
        fill="{color}"
        stroke="#100A10"
    />
    """


svg += text(
    "MORE",
    legend_x + 330,
    legend_y + 47,
    15,
    "#E875A0",
    "700"
)


# ============================================================
# STAT CARDS
# ============================================================

stats = [
    ("⚡", total_contributions, "Contributions"),
    ("▣", public_repos, "Public Repos"),
    ("◷", months_active, "Months"),
    ("☆", total_stars, "Stars")
]


card_x = 670
card_y = 640
card_width = 165
card_height = 80
card_gap = 16


for i, (icon, value, label) in enumerate(stats):

    x = card_x + i * (
        card_width + card_gap
    )

    svg += f"""
    <rect
        x="{x}"
        y="{card_y}"
        width="{card_width}"
        height="{card_height}"
        rx="14"
        fill="#0B080E"
        stroke="#A83B68"
        stroke-width="1.2"
    />
    """

    svg += text(
        icon,
        x + 18,
        card_y + 35,
        24,
        "#F078A7",
        "600"
    )

    svg += text(
        value,
        x + 55,
        card_y + 34,
        23,
        "#FFFFFF",
        "700"
    )

    svg += text(
        label,
        x + 55,
        card_y + 58,
        12,
        "#D99AAF",
        "400"
    )


# ============================================================
# FOOTER
# ============================================================

svg += text(
    "GitHub activity • automatically updated",
    55,
    875,
    12,
    "#80616F",
    "400"
)


svg += """
</svg>
"""


# ============================================================
# WRITE FILE
# ============================================================

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as file:

    file.write(svg)


print(
    f"Activity Trail generated for {USERNAME}"
)

print(
    f"Contributions: {total_contributions}"
)

print(
    f"Public repositories: {public_repos}"
)

print(
    f"Stars: {total_stars}"
)
