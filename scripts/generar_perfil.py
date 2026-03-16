import os
import requests
from datetime import datetime

# GitHub API setup
TOKEN = os.environ.get("GH_TOKEN")
USERNAME = "marcosvil01"
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

def get_github_stats():
    """Fetches stats using GitHub GraphQL API"""
    if not TOKEN:
        print("⚠ No GH_TOKEN found. Using mock data for design preview.")
        return {
            "name": "Marcos",
            "commits": 1337,
            "stars": 42,
            "prs": 15,
            "issues": 8,
            "followers": 12,
            "contribs_last_year": 520,
            "top_languages": [
                {"name": "Java", "color": "#b07219", "percentage": 35},
                {"name": "Python", "color": "#3572A5", "percentage": 25},
                {"name": "TypeScript", "color": "#3178c6", "percentage": 20},
                {"name": "JavaScript", "color": "#f1e05a", "percentage": 12},
                {"name": "HTML", "color": "#e34c26", "percentage": 8},
            ]
        }

    query = """
    query {
      user(login: "%s") {
        name
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER, orderBy: {direction: DESC, field: STARGAZERS}) {
          totalCount
          nodes {
            stargazers { totalCount }
            languages(first: 5, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
        contributionsCollection {
          contributionCalendar { totalContributions }
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
        }
      }
    }
    """ % USERNAME

    response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Query failed: {response.status_code}")

    data = response.json()["data"]["user"]
    stars = sum(r["stargazers"]["totalCount"] for r in data["repositories"]["nodes"])

    langs = {}
    total_size = 0
    for repo in data["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            size = edge["size"]
            color = edge["node"]["color"]
            langs[name] = {"size": langs.get(name, {}).get("size", 0) + size, "color": color or "#ccc"}
            total_size += size

    top_langs = sorted(
        [{"name": k, "color": v["color"], "percentage": round((v["size"]/total_size)*100)}
         for k, v in langs.items() if total_size > 0],
        key=lambda x: x["percentage"], reverse=True
    )[:6]

    return {
        "name": data["name"] or USERNAME,
        "commits": data["contributionsCollection"]["totalCommitContributions"],
        "stars": stars,
        "prs": data["contributionsCollection"]["totalPullRequestContributions"],
        "issues": data["contributionsCollection"]["totalIssueContributions"],
        "followers": data["followers"]["totalCount"],
        "contribs_last_year": data["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "top_languages": top_langs
    }


def create_svg(stats):
    """
    Generates a responsive Cyber/HUD SVG.
    Width is fixed at 888px (GitHub profile container).
    Height adapts to the number of languages detected.
    Layout is vertical: Header → Stats → Languages → Modules.
    """
    W = 888
    PAD = 24        # outer padding
    INNER = W - 2 * PAD  # usable inner width

    # Colors
    BG      = "#030A16"
    PANEL   = "#0B1928"
    GREEN   = "#00FF41"
    CYAN    = "#00E5FF"
    PURPLE  = "#B026FF"
    ORANGE  = "#FF9900"
    WHITE   = "#E0E6ED"
    MUTED   = "#5B7C99"

    # ---- Calculate dynamic heights ----
    header_h = 100
    stats_h  = 160
    num_langs = len(stats["top_languages"])
    lang_row_h = 38
    langs_h  = 60 + num_langs * lang_row_h   # title + rows
    modules_h = 170
    gap = 16

    H = PAD + header_h + gap + stats_h + gap + langs_h + gap + modules_h + PAD

    # Y positions for each section
    y_header  = PAD
    y_stats   = y_header + header_h + gap
    y_langs   = y_stats + stats_h + gap
    y_modules = y_langs + langs_h + gap

    # CSS for animated bars
    bar_w_max = INNER - 180  # space for bar after label
    bar_css = ""
    for i, lang in enumerate(stats["top_languages"]):
        bw = int(bar_w_max * (lang["percentage"] / 100))
        bar_css += f"""
        @keyframes fb{i} {{ 0%{{width:0;opacity:0}} 100%{{width:{bw}px;opacity:1}} }}
        .b{i}{{animation:fb{i} 1.2s cubic-bezier(.1,.8,.2,1) forwards;animation-delay:{0.4+i*0.15}s;width:0}}
        """

    svg = f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#02050A"/><stop offset="50%" stop-color="#051021"/><stop offset="100%" stop-color="#020611"/>
  </linearGradient>
  <linearGradient id="pg" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="rgba(11,25,44,0.92)"/><stop offset="100%" stop-color="rgba(4,10,20,0.92)"/>
  </linearGradient>
  <filter id="gG"><feGaussianBlur stdDeviation="3" result="b"/><feComposite in="SourceGraphic" in2="b" operator="over"/></filter>
  <filter id="gB"><feGaussianBlur stdDeviation="3" result="b"/><feComposite in="SourceGraphic" in2="b" operator="over"/></filter>
  <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
    <path d="M50 0L0 0 0 50" fill="none" stroke="rgba(0,229,255,0.04)" stroke-width="1"/>
    <circle cx="50" cy="50" r="1" fill="rgba(0,229,255,0.12)"/>
  </pattern>
</defs>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600;700&amp;family=Orbitron:wght@500;700;900&amp;display=swap');
  .t1{{font:800 26px 'Orbitron',sans-serif;fill:{WHITE};letter-spacing:2px}}
  .t2{{font:700 14px 'Fira Code',monospace;fill:{CYAN};letter-spacing:1px}}
  .t3{{font:600 13px 'Fira Code',monospace;fill:{MUTED};letter-spacing:1px}}
  .t4{{font:700 22px 'Orbitron',sans-serif;fill:{CYAN}}}
  .t5{{font:400 13px 'Fira Code',monospace;fill:{WHITE}}}
  .t6{{font:400 11px 'Fira Code',monospace;fill:rgba(0,255,65,0.45)}}
  .blink{{animation:bk 1s step-end infinite;fill:{GREEN};font-weight:700}}
  @keyframes bk{{50%{{opacity:0}}}}
  @keyframes fadeUp{{0%{{opacity:0;transform:translateY(6px)}}100%{{opacity:1;transform:translateY(0)}}}}
  .anim{{animation:fadeUp .5s ease-out forwards}}
  {bar_css}
</style>

<!-- Background -->
<rect width="{W}" height="{H}" rx="12" fill="url(#bg)" stroke="{CYAN}" stroke-width="1"/>
<rect width="{W}" height="{H}" fill="url(#grid)"/>

<!-- Top line -->
<path d="M0 28 L28 0 L150 0 L170 20 L{W} 20" fill="none" stroke="rgba(0,229,255,0.3)" stroke-width="1"/>
<text x="36" y="15" class="t6">sys.boot(user="{USERNAME}")</text>

<!-- Corner marks -->
<polygon points="10,10 28,10 28,15 15,15 15,28 10,28" fill="{CYAN}"/>
<polygon points="{W-10},{H-10} {W-28},{H-10} {W-28},{H-15} {W-15},{H-15} {W-15},{H-28} {W-10},{H-28}" fill="{PURPLE}"/>

<!-- Binary hints -->
<text x="{W-168}" y="46" class="t6" style="opacity:.45">01001101 01100001</text>
<text x="{W-140}" y="62" class="t6" style="opacity:.3">01110010 01100011</text>

<!-- ============================================ -->
<!-- SECTION 1: HEADER / IDENTITY                 -->
<!-- ============================================ -->
<g class="anim" style="animation-delay:.1s">
  <rect x="{PAD}" y="{y_header}" width="{INNER}" height="{header_h}" rx="8" fill="url(#pg)" stroke="{CYAN}" stroke-width="1" stroke-opacity=".4"/>

  <!-- Avatar circle -->
  <circle cx="{PAD+60}" cy="{y_header+header_h//2}" r="38" fill="rgba(0,229,255,0.04)" stroke="{CYAN}" stroke-width="2" stroke-dasharray="4 2"/>
  <circle cx="{PAD+60}" cy="{y_header+header_h//2}" r="32" fill="rgba(0,255,65,0.08)"/>
  <text x="{PAD+46}" y="{y_header+header_h//2+10}" class="t1" font-size="30" fill="{GREEN}" filter="url(#gG)">M<tspan font-size="20">.</tspan></text>

  <!-- Name & Role -->
  <text x="{PAD+120}" y="{y_header+35}" class="t2" font-size="16">{stats['name'].upper()}</text>
  <text x="{PAD+120}" y="{y_header+58}" class="t3"><tspan fill="{WHITE}">Role: </tspan><tspan fill="{PURPLE}">FULLSTACK_DEV</tspan></text>
  <text x="{PAD+120}" y="{y_header+80}" class="t3"><tspan fill="{WHITE}">Status: </tspan><tspan fill="{ORANGE}">CODING</tspan><tspan class="blink">_</tspan></text>

  <!-- Date -->
  <text x="{W-PAD-10}" y="{y_header+80}" class="t6" text-anchor="end">v{datetime.now().strftime('%Y.%m.%d')}</text>
</g>

<!-- ============================================ -->
<!-- SECTION 2: CORE STATS (4 boxes in a row)     -->
<!-- ============================================ -->
<g class="anim" style="animation-delay:.2s">
  <rect x="{PAD}" y="{y_stats}" width="{INNER}" height="{stats_h}" rx="8" fill="url(#pg)" stroke="{MUTED}" stroke-width="1" stroke-opacity=".25"/>
  <text x="{PAD+16}" y="{y_stats+28}" class="t2">> CORE_METRICS</text>
"""

    # 4 stat boxes side by side
    stat_items = [
        ("COMMITS",        stats["commits"],           GREEN),
        ("STARS",          stats["stars"],              CYAN),
        ("PULL REQUESTS",  stats["prs"],                PURPLE),
        ("ISSUES",         stats["issues"],             ORANGE),
    ]
    box_w = (INNER - 16 * 5) // 4  # 4 boxes with gaps
    box_h = 90
    box_y = y_stats + 48

    for idx, (label, value, color) in enumerate(stat_items):
        bx = PAD + 16 + idx * (box_w + 16)
        svg += f"""
  <rect x="{bx}" y="{box_y}" width="{box_w}" height="{box_h}" rx="6" fill="#060D18" stroke="{color}" stroke-width="1" stroke-opacity=".5"/>
  <text x="{bx + box_w//2}" y="{box_y + 28}" class="t3" text-anchor="middle" fill="{MUTED}">{label}</text>
  <text x="{bx + box_w//2}" y="{box_y + 62}" class="t4" text-anchor="middle" fill="{color}" filter="url(#gB)">{value}</text>
  <rect x="{bx + 10}" y="{box_y + box_h - 12}" width="{box_w - 20}" height="2" rx="1" fill="{color}" opacity=".3"/>
"""

    # Annual contribs badge
    svg += f"""
  <text x="{W-PAD-16}" y="{y_stats+28}" class="t3" text-anchor="end" fill="{GREEN}">+{stats['contribs_last_year']} this year</text>
</g>

<!-- ============================================ -->
<!-- SECTION 3: LANGUAGES (responsive rows)       -->
<!-- ============================================ -->
<g class="anim" style="animation-delay:.35s">
  <rect x="{PAD}" y="{y_langs}" width="{INNER}" height="{langs_h}" rx="8" fill="url(#pg)" stroke="{MUTED}" stroke-width="1" stroke-opacity=".25"/>
  <text x="{PAD+16}" y="{y_langs+28}" class="t2" fill="{PURPLE}">// RUNTIME_METRICS::LANGUAGES</text>
  <text x="{W-PAD-16}" y="{y_langs+28}" class="t6" fill="{MUTED}" text-anchor="end">{num_langs} detected</text>
  <rect x="{PAD+16}" y="{y_langs+38}" width="{INNER-32}" height="1" fill="rgba(176,38,255,0.25)"/>
"""

    ly = y_langs + 52
    label_w = 140
    pct_w = 40
    bar_x = PAD + 16 + label_w
    for i, lang in enumerate(stats["top_languages"]):
        svg += f"""
  <g class="anim" style="animation-delay:{0.4+i*0.08}s">
    <text x="{PAD+16}" y="{ly+14}" class="t5">{lang['name']}</text>
    <text x="{W-PAD-16}" y="{ly+14}" class="t5" fill="{lang['color']}" text-anchor="end">{lang['percentage']}%</text>
    <rect x="{bar_x}" y="{ly+4}" width="{bar_w_max - pct_w}" height="7" rx="3" fill="#0A1220"/>
    <rect x="{bar_x}" y="{ly+4}" height="7" rx="3" fill="{lang['color']}" class="b{i}"/>
    <rect x="{bar_x}" y="{ly+4}" height="7" rx="3" fill="{lang['color']}" opacity=".4" filter="url(#gB)" class="b{i}"/>
  </g>
"""
        ly += lang_row_h

    svg += f"""
</g>

<!-- ============================================ -->
<!-- SECTION 4: SYSTEM MODULES / HOBBIES          -->
<!-- ============================================ -->
<g class="anim" style="animation-delay:.6s">
  <rect x="{PAD}" y="{y_modules}" width="{INNER}" height="{modules_h}" rx="8" fill="url(#pg)" stroke="{ORANGE}" stroke-width="1" stroke-opacity=".35"/>
  <text x="{PAD+16}" y="{y_modules+28}" class="t2" fill="{ORANGE}">[+] SYSTEM_MODULES</text>
  <text x="{W-PAD-16}" y="{y_modules+28}" class="t6" fill="{MUTED}" text-anchor="end">4 mounted</text>
"""

    # 4 module slots
    slot_labels = [
        ("MOD.DEV",  "CODING",  GREEN),
        ("MOD.GAME", "GAMING",  CYAN),
        ("MOD.STRG", "FITNESS", ORANGE),
        ("MOD.WILD", "NATURE",  PURPLE),
    ]
    slot_w = (INNER - 16 * 5) // 4
    slot_h = 110
    slot_y = y_modules + 42

    for idx, (mod_name, label, color) in enumerate(slot_labels):
        sx = PAD + 16 + idx * (slot_w + 16)
        cx = sx + slot_w // 2
        svg += f"""
  <path d="M{sx+8} {slot_y} L{sx+slot_w-8} {slot_y} L{sx+slot_w} {slot_y+8} L{sx+slot_w} {slot_y+slot_h-8} L{sx+slot_w-8} {slot_y+slot_h} L{sx+8} {slot_y+slot_h} L{sx} {slot_y+slot_h-8} L{sx} {slot_y+8} Z" fill="#060D18" stroke="{color}" stroke-width="1.5"/>
  <text x="{cx}" y="{slot_y+20}" class="t6" text-anchor="middle" fill="{color}">{mod_name}</text>
  <text x="{cx}" y="{slot_y+slot_h-10}" class="t5" text-anchor="middle">{label}</text>
"""

    # Icon for CODING (laptop)
    s0x = PAD + 16
    c0 = s0x + slot_w // 2
    svg += f"""
  <rect x="{c0-25}" y="{slot_y+40}" width="50" height="28" rx="3" fill="none" stroke="{GREEN}" stroke-width="2"/>
  <path d="M{c0-35} {slot_y+72} L{c0+35} {slot_y+72} L{c0+38} {slot_y+76} L{c0-38} {slot_y+76} Z" fill="{GREEN}"/>
  <text x="{c0-18}" y="{slot_y+60}" class="t3" font-size="10" fill="{GREEN}">>_</text>
"""

    # Icon for GAMING (controller)
    s1x = PAD + 16 + (slot_w + 16)
    c1 = s1x + slot_w // 2
    svg += f"""
  <path d="M{c1-22} {slot_y+56} Q{c1-22} {slot_y+38},{c1} {slot_y+38} Q{c1+22} {slot_y+38},{c1+22} {slot_y+56} L{c1+22} {slot_y+64} Q{c1+22} {slot_y+76},{c1+12} {slot_y+76} L{c1+8} {slot_y+62} L{c1-8} {slot_y+62} L{c1-12} {slot_y+76} Q{c1-22} {slot_y+76},{c1-22} {slot_y+64} Z" fill="none" stroke="{CYAN}" stroke-width="2"/>
  <circle cx="{c1-10}" cy="{slot_y+56}" r="3.5" fill="{CYAN}"/>
  <circle cx="{c1+8}" cy="{slot_y+48}" r="2" fill="{CYAN}"/>
  <circle cx="{c1+14}" cy="{slot_y+54}" r="2" fill="{CYAN}"/>
"""

    # Icon for FITNESS (dumbbell)
    s2x = PAD + 16 + 2 * (slot_w + 16)
    c2 = s2x + slot_w // 2
    svg += f"""
  <rect x="{c2-26}" y="{slot_y+55}" width="52" height="6" rx="2" fill="{ORANGE}"/>
  <rect x="{c2-22}" y="{slot_y+46}" width="9" height="24" rx="1" fill="none" stroke="{ORANGE}" stroke-width="2"/>
  <rect x="{c2+13}" y="{slot_y+46}" width="9" height="24" rx="1" fill="none" stroke="{ORANGE}" stroke-width="2"/>
"""

    # Icon for NATURE (tree + paw)
    s3x = PAD + 16 + 3 * (slot_w + 16)
    c3 = s3x + slot_w // 2
    svg += f"""
  <path d="M{c3} {slot_y+35} L{c3-14} {slot_y+58} L{c3-5} {slot_y+58} L{c3-16} {slot_y+76} L{c3+16} {slot_y+76} L{c3+5} {slot_y+58} L{c3+14} {slot_y+58} Z" fill="none" stroke="{PURPLE}" stroke-width="2"/>
  <circle cx="{c3+20}" cy="{slot_y+45}" r="3" fill="{PURPLE}"/>
  <circle cx="{c3+14}" cy="{slot_y+40}" r="2" fill="{PURPLE}"/>
  <circle cx="{c3+26}" cy="{slot_y+40}" r="2" fill="{PURPLE}"/>
"""

    svg += f"""
</g>

</svg>"""
    return svg




def create_about_me_svg():
    return """<svg width="888" height="200" viewBox="0 0 888 200" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="aboutBg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#0B0E17"/>
    <stop offset="100%" stop-color="#0D1420"/>
  </linearGradient>
</defs>

<style>
  @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&amp;family=Inter:wght@400;500;600&amp;display=swap');
  @keyframes fadeIn { 0%{opacity:0;transform:translateY(6px)} 100%{opacity:1;transform:translateY(0)} }
  .fade { animation: fadeIn 0.8s ease-out forwards; }
</style>

<rect width="888" height="200" rx="10" fill="url(#aboutBg)" stroke="#1E293B" stroke-width="1"/>
<rect x="0" y="0" width="3" height="200" rx="1" fill="#00E5FF" opacity="0.4"/>

<text x="32" y="36" font-family="'Fira Code',monospace" font-size="13" fill="#00E5FF" letter-spacing="2" opacity="0.7" class="fade">// ABOUT_ME</text>
<line x1="32" y1="46" x2="856" y2="46" stroke="#1E293B" stroke-width="1"/>

<g class="fade" style="animation-delay:0.1s">
  <text x="32" y="78" font-family="'Inter','Segoe UI',sans-serif" font-size="15" fill="#E0E6ED">
    <tspan>Hi, I'm </tspan>
    <tspan fill="#00E5FF" font-weight="600">Marcos</tspan>
    <tspan> — a fullstack developer from Spain.</tspan>
  </text>
</g>

<g class="fade" style="animation-delay:0.15s">
  <text x="32" y="104" font-family="'Inter','Segoe UI',sans-serif" font-size="14" fill="#94A3B8">
    I build things for the web and enjoy turning ideas into clean, functional code.
  </text>
</g>

<g class="fade" style="animation-delay:0.2s">
  <text x="32" y="130" font-family="'Inter','Segoe UI',sans-serif" font-size="14" fill="#94A3B8">
    Outside of coding, you'll find me at the gym, outdoors in nature,
  </text>
</g>

<g class="fade" style="animation-delay:0.25s">
  <text x="32" y="152" font-family="'Inter','Segoe UI',sans-serif" font-size="14" fill="#94A3B8">
    playing Minecraft or CoD, or hanging out with my dog.
  </text>
</g>

<g class="fade" style="animation-delay:0.35s">
  <rect x="32" y="170" width="55" height="22" rx="4" fill="none" stroke="#00E5FF" stroke-width="1" opacity="0.5"/>
  <text x="59" y="185" text-anchor="middle" font-family="'Fira Code',monospace" font-size="10" fill="#00E5FF" opacity="0.8">code</text>
  
  <rect x="97" y="170" width="68" height="22" rx="4" fill="none" stroke="#B026FF" stroke-width="1" opacity="0.5"/>
  <text x="131" y="185" text-anchor="middle" font-family="'Fira Code',monospace" font-size="10" fill="#B026FF" opacity="0.8">gaming</text>
  
  <rect x="175" y="170" width="68" height="22" rx="4" fill="none" stroke="#FF9900" stroke-width="1" opacity="0.5"/>
  <text x="209" y="185" text-anchor="middle" font-family="'Fira Code',monospace" font-size="10" fill="#FF9900" opacity="0.8">fitness</text>
  
  <rect x="253" y="170" width="65" height="22" rx="4" fill="none" stroke="#00FF41" stroke-width="1" opacity="0.5"/>
  <text x="285" y="185" text-anchor="middle" font-family="'Fira Code',monospace" font-size="10" fill="#00FF41" opacity="0.8">nature</text>
  
  <rect x="328" y="170" width="55" height="22" rx="4" fill="none" stroke="#F0ECE4" stroke-width="1" opacity="0.4"/>
  <text x="355" y="185" text-anchor="middle" font-family="'Fira Code',monospace" font-size="10" fill="#F0ECE4" opacity="0.7">dogs</text>
</g>
</svg>"""

def main():
    print("Fetching stats...")
    stats = get_github_stats()
    
    print("Generating SVGs...")
    os.makedirs("dist", exist_ok=True)
    
    with open("dist/perfil_hud.svg", "w", encoding="utf-8") as f:
        f.write(create_svg(stats))
        
    with open("dist/about_me.svg", "w", encoding="utf-8") as f:
        f.write(create_about_me_svg())
        
    print(f"✅ Generated dist/perfil_hud.svg ({len(stats['top_languages'])} languages detected)")
    print("✅ Generated dist/about_me.svg")
    print("⚠️  Para generar el banner, ejecuta: python scripts/generar_banner.py")

if __name__ == "__main__":
    main()
