import os
import sys
import requests

USERNAME = os.environ.get("GITHUB_USER", "shroukmohamed5")
TOKEN = os.environ.get("GITHUB_TOKEN")

HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
API = "https://api.github.com"

LANGUAGE_COLORS = {
    "Java": "#b07219",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Jupyter Notebook": "#DA5B0B",
    "C": "#555555",
    "C++": "#f34b7d",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Vue": "#41b883",
    "PLpgSQL": "#336790",
    "Assembly": "#6E4C13",
}
DEFAULT_COLOR = "#8b8b8b"


def paginated_logins(endpoint):
    logins = set()
    page = 1
    while True:
        r = requests.get(
            f"{API}/users/{USERNAME}/{endpoint}",
            headers=HEADERS,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        logins.update(item["login"] for item in data)
        if len(data) < 100:
            break
        page += 1
    return logins


def get_user_info():
    r = requests.get(f"{API}/users/{USERNAME}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def get_repo_stats():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"{API}/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1

    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    lang_bytes = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            lr = requests.get(repo["languages_url"], headers=HEADERS, timeout=30)
            lr.raise_for_status()
            for lang, size in lr.json().items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + size
        except Exception:
            continue

    return repos, total_stars, lang_bytes


def top_languages(lang_bytes, top_n=5):
    total = sum(lang_bytes.values()) or 1
    items = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:top_n]
    result = []
    for lang, size in items:
        pct = round(size / total * 100, 1)
        color = LANGUAGE_COLORS.get(lang, DEFAULT_COLOR)
        result.append((lang, pct, color))
    return result


def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(user_info, repo_count, star_count, langs, followers, following, mutuals, dont_follow_back, you_dont_follow):
    W, H = 900, 300
    bg = "#0f2247"
    panel = "#132a52"
    border = "#1e3a66"
    text_light = "#ffffff"
    text_dim = "#9fb3d1"
    accent = "#00d4ff"

    avatar_url = user_info.get("avatar_url", "")
    name = f"@{USERNAME}"

    # Language bar segments
    bar_x, bar_y, bar_w, bar_h = 260, 55, 590, 14
    segments = []
    legend = []
    cursor = bar_x
    if not langs:
        segments.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="7" fill="{border}"/>')
    else:
        for lang, pct, color in langs:
            seg_w = bar_w * (pct / 100)
            segments.append(f'<rect x="{cursor:.1f}" y="{bar_y}" width="{max(seg_w,2):.1f}" height="{bar_h}" fill="{color}"/>')
            cursor += seg_w
        legend_x = bar_x
        legend_y = bar_y + 34
        for i, (lang, pct, color) in enumerate(langs):
            lx = legend_x + (i % 3) * 195
            ly = legend_y + (i // 3) * 26
            legend.append(
                f'<circle cx="{lx}" cy="{ly-5}" r="5" fill="{color}"/>'
                f'<text x="{lx+12}" y="{ly}" font-family="Segoe UI, Verdana, sans-serif" font-size="13" fill="{text_light}">{esc(lang)} {pct}%</text>'
            )

    # Stat boxes
    stats = [
        ("Followers", followers, "#2ee6a6"),
        ("Following", following, "#7c83fd"),
        ("Mutuals", mutuals, "#c084fc"),
        ("Don't follow back", dont_follow_back, "#ff6b6b"),
        ("You don't follow", you_dont_follow, "#ffb454"),
    ]
    box_w = 158
    box_h = 100
    gap = 14
    total_boxes_w = box_w * 5 + gap * 4
    start_x = (W - total_boxes_w) / 2
    box_y = 150

    box_svgs = []
    for i, (label, value, color) in enumerate(stats):
        x = start_x + i * (box_w + gap)
        box_svgs.append(f'''
        <rect x="{x:.1f}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="{panel}" stroke="{border}" stroke-width="1"/>
        <text x="{x + box_w/2:.1f}" y="{box_y + 46}" font-family="Segoe UI, Verdana, sans-serif" font-size="30" font-weight="700" fill="{color}" text-anchor="middle">{value}</text>
        <text x="{x + box_w/2:.1f}" y="{box_y + 74}" font-family="Segoe UI, Verdana, sans-serif" font-size="13" fill="{text_dim}" text-anchor="middle">{esc(label)}</text>
        ''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <clipPath id="avatarClip">
      <circle cx="70" cy="65" r="42"/>
    </clipPath>
    <style>
      text {{ font-family: 'Segoe UI', Verdana, sans-serif; }}
    </style>
  </defs>
  <rect x="0" y="0" width="{W}" height="{H}" rx="18" fill="{bg}"/>
  <rect x="10" y="10" width="{W-20}" height="115" rx="16" fill="{panel}" stroke="{border}" stroke-width="1"/>

  <circle cx="70" cy="65" r="44" fill="{border}"/>
  <image href="{avatar_url}" x="28" y="23" width="84" height="84" clip-path="url(#avatarClip)"/>

  <text x="128" y="58" font-size="20" font-weight="700" fill="{text_light}">{esc(name)}</text>
  <text x="128" y="80" font-size="13" fill="{text_dim}">{repo_count} repositories &#183; &#9733; {star_count}</text>

  {''.join(segments)}
  {''.join(legend)}

  {''.join(box_svgs)}
</svg>'''
    return svg


def main():
    user_info = get_user_info()
    followers_set = paginated_logins("followers")
    following_set = paginated_logins("following")

    mutuals = followers_set & following_set
    dont_follow_back = following_set - followers_set
    you_dont_follow = followers_set - following_set

    repos, star_count, lang_bytes = get_repo_stats()
    langs = top_languages(lang_bytes, top_n=5)

    svg = build_svg(
        user_info=user_info,
        repo_count=user_info.get("public_repos", len(repos)),
        star_count=star_count,
        langs=langs,
        followers=len(followers_set),
        following=len(following_set),
        mutuals=len(mutuals),
        dont_follow_back=len(dont_follow_back),
        you_dont_follow=len(you_dont_follow),
    )

    os.makedirs("dist", exist_ok=True)
    with open("dist/dashboard.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    print("Dashboard generated: dist/dashboard.svg")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error generating dashboard: {e}", file=sys.stderr)
        sys.exit(1)
