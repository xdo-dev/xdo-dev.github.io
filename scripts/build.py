#!/usr/bin/env python3
"""Build the xdo website.

Zero dependencies: standard-library Python only (3.8+).

What it does:
- Reads company copy from content.json (English + Traditional Chinese)
- Reads articles from articles/<lang>/*.md (front matter + Markdown)
- Renders the static site into site/
- Copies assets/ into site/assets/
- Writes sitemap.xml, robots.txt and 404.html
- Cleans stale files from previous builds using a manifest
  (no wholesale folder deletion, which can fail on Windows)

Usage:
    python3 scripts/build.py
"""

import json
import re
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
MANIFEST = OUT / ".build-manifest.json"

ICON_SUN = (
    '<svg class="icon-sun" viewBox="0 0 24 24" aria-hidden="true">'
    '<circle cx="12" cy="12" r="5"/>'
    '<path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42'
    'M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
)
ICON_MOON = (
    '<svg class="icon-moon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
)


# ---------------------------------------------------------------------------
# Markdown (small subset: headings, paragraphs, lists, code, quotes, inline)
# ---------------------------------------------------------------------------

INLINE_PATTERNS = [
    (re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)"), r'<a href="\2">\1</a>'),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)"), r"<em>\1</em>"),
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
]


def inline(text: str) -> str:
    """Escape HTML, then apply inline Markdown."""
    text = escape(text, quote=False)
    for pattern, repl in INLINE_PATTERNS:
        text = pattern.sub(repl, text)
    return text


def render_markdown(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    html_out = []
    i = 0
    in_code = False
    code_lines = []
    list_type = None  # "ul" | "ol" | None

    def close_list():
        nonlocal list_type
        if list_type:
            html_out.append(f"</{list_type}>")
            list_type = None

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                html_out.append(
                    "<pre><code>" + escape("\n".join(code_lines), quote=False) + "</code></pre>"
                )
                code_lines = []
                in_code = False
            else:
                close_list()
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not stripped:
            close_list()
            i += 1
            continue

        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            close_list()
            level = len(m.group(1)) + 1  # h2-h4 (title is the page h1)
            html_out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        m = re.match(r"^>\s?(.*)$", stripped)
        if m:
            close_list()
            html_out.append(f"<blockquote><p>{inline(m.group(1))}</p></blockquote>")
            i += 1
            continue

        if re.match(r"^(---|\*\*\*)$", stripped):
            close_list()
            html_out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^[-*]\s+(.*)$", stripped)
        if m:
            if list_type != "ul":
                close_list()
                html_out.append("<ul>")
                list_type = "ul"
            html_out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue

        m = re.match(r"^\d+\.\s+(.*)$", stripped)
        if m:
            if list_type != "ol":
                close_list()
                html_out.append("<ol>")
                list_type = "ol"
            html_out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue

        # paragraph: consume consecutive plain lines
        close_list()
        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (
                not nxt
                or nxt.startswith(("#", ">", "```", "- ", "* ", "---"))
                or re.match(r"^\d+\.\s", nxt)
            ):
                break
            para.append(nxt)
            i += 1
        html_out.append("<p>" + inline(" ".join(para)) + "</p>")

    close_list()
    if in_code:
        html_out.append(
            "<pre><code>" + escape("\n".join(code_lines), quote=False) + "</code></pre>"
        )
    return "\n".join(html_out)


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------

def parse_article(path: Path):
    """Parse front matter + body. Returns dict or None if unparsable."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---"):
        return None
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return None
    meta = {}
    for line in parts[0][3:].strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip('"')
    return {
        "slug": path.stem,
        "title": meta.get("title", path.stem),
        "description": meta.get("description", ""),
        "date": meta.get("date", ""),
        "draft": meta.get("draft", "").lower() == "true",
        "body": render_markdown(parts[1].strip()),
    }


def load_articles(lang_dir: Path):
    articles = []
    if not lang_dir.is_dir():
        return articles
    for path in sorted(lang_dir.glob("*.md")):
        parsed = parse_article(path)
        if parsed:
            articles.append(parsed)
    return articles


def date_sort_key(article):
    try:
        return tuple(int(x) for x in article["date"].split("-"))
    except ValueError:
        return (0, 0, 0)


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------

def render(template: str, values: dict) -> str:
    html = template
    for key, value in values.items():
        html = html.replace("{{" + key + "}}", str(value))
    leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", html)
    if leftover:
        raise ValueError(f"Unresolved template tokens: {sorted(set(leftover))}")
    return html


def build():
    content = json.loads((ROOT / "content.json").read_text(encoding="utf-8"))
    site = content["site"]
    articles_enabled = site.get("articles_enabled", True)

    templates = {
        "home": (ROOT / "templates" / "home.html").read_text(
            encoding="utf-8"
        ),
    }

    if articles_enabled:
        templates["article_list"] = (
            ROOT / "templates" / "article-list.html"
        ).read_text(encoding="utf-8")

        templates["article"] = (
            ROOT / "templates" / "article.html"
        ).read_text(encoding="utf-8")

    generated = []  # paths written this build, relative to OUT

    def write_page(rel_path: Path, html: str):
        target = OUT / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        generated.append(rel_path.as_posix())

    articles_by_lang = {
        lang: [a for a in load_articles(ROOT / "articles" / lang) if not a["draft"]]
        for lang in ("en", "zh-Hant")
    }
    for lang in articles_by_lang:
        articles_by_lang[lang].sort(key=date_sort_key, reverse=True)

    base_url = f"https://{site['domain']}/"
    articles_enabled = site.get("articles_enabled", True)

    def other_page_url(lang: str, depth: int, target_rel: str) -> str:
        """URL of a page in the OTHER language, seen from `depth` levels deep.

        target_rel is the page path relative to the site root
        (e.g. "index.html", "articles/index.html").
        """
        if lang == "en":
            return "../" * depth + "zh-Hant/" + target_rel
        return "../" * depth + target_rel

    def common_values(c: dict, depth: int, canonical: str, other_canonical: str) -> dict:
        """Values shared by every page of one language, at a given folder depth.

        depth = number of levels below the site root
        (index.html -> 0, articles/index.html -> 1, articles/x/index.html -> 2)
        """
        p = "../" * depth
        other = content[c["other_lang_code"]]
        lang_root = "" if c["lang_code"] == "en" else "zh-Hant/"
        return {
            "HTML_LANG": c["html_lang"],
            "OTHER_HTML_LANG": other["html_lang"],
            "TITLE": c["title"],
            "DESCRIPTION": c["description"],
            "ASSETS": p + "assets",
            "HOME_URL": p + lang_root + "index.html",
            "ARTICLES_URL": p + lang_root + "articles/index.html",
            "OTHER_HOME_URL": other_page_url(lang, depth, "index.html"),
            "MENU": c["menu"],
            "THEME_TOGGLE": c["theme_toggle"],
            "ICON_SUN": ICON_SUN,
            "ICON_MOON": ICON_MOON,
            "YEAR": date.today().year,
            "COMPANY": site["company"],
            "BRAND": site["brand"],
            "GITHUB_URL": site["github"],
            "EMAIL": site["email"],
            "FOOTER_TAGLINE": c["footer"]["tagline"],
            "FOOTER_RIGHTS": c["footer"]["rights"],
            "FOOTER_OFFICE": c["footer"]["office_placeholder"],
            "OTHER_LANG_LABEL": c["other_lang_label"],
            "ARTICLES_LABEL": c["articles_page"]["label"],
            "CANONICAL": canonical,
            "OTHER_CANONICAL": other_canonical,
        }

    def nav_fragments(c: dict, common: dict, current_is_articles: bool = False) -> dict:
        nav_labels = {n["id"]: n["label"] for n in c["nav"]}
        return {
            "NAV_SERVICES": nav_labels["services"],
            "NAV_APPROACH": nav_labels["approach"],
            "NAV_ABOUT": nav_labels["about"],
            "NAV_ARTICLES": nav_labels["articles"],
            "NAV_CONTACT": nav_labels["contact"],
        }

    for lang in ("en", "zh-Hant"):
        c = content[lang]
        lang_path = "" if lang == "en" else f"{lang}/"
        home_depth = 0 if lang == "en" else 1
        home_canonical = base_url + ("" if lang == "en" else f"{lang}/")
        other_home_canonical = base_url + ("" if lang != "en" else "zh-Hant/")

        # --- home page ---------------------------------------------------
        common = common_values(c, home_depth, home_canonical, other_home_canonical)
        nav_links = []
        for item in c["nav"]:
            if item.get("href_kind") == "articles":
                if not articles_enabled:
                    continue
                nav_links.append(f'<a href="{common["ARTICLES_URL"]}">{item["label"]}</a>')
            else:
                nav_links.append(f'<a href="{common["HOME_URL"]}#{item["id"]}">{item["label"]}</a>')
        service_cards = []
        for s in c["services"]["items"]:
            service_cards.append(
                f'''      <div class="card">
        <p class="card-tag">{s["tag"]}</p>
        <h3>{s["name"]}</h3>
        <p>{s["desc"]}</p>
        <p class="who">{s["who"]}</p>
        <div class="benefit"><strong>{s["benefit_title"]}</strong>{s["benefit"]}</div>
      </div>'''
            )
        steps = []
        for s in c["approach"]["steps"]:
            steps.append(
                f'''      <div class="step">
        <p class="step-num">{s["step"]}</p>
        <h3>{s["name"]}</h3>
        <p>{s["desc"]}</p>
      </div>'''
            )
        creds = "\n".join(f"          <li>{cred}</li>" for cred in c["about"]["credentials"])

        home_values = dict(common)
        home_values.update(
            {
                "NAV_LINKS": "\n      ".join(nav_links),
                "HERO_EYEBROW": c["hero"]["eyebrow"],
                "HERO_TITLE": "<br>".join(c["hero"]["title_lines"]),
                "HERO_LEAD": c["hero"]["lead"],
                "HERO_CTA_PRIMARY": c["hero"]["cta_primary"],
                "ARTICLES_CTA": (
                    f'      <a class="btn" href="{common["ARTICLES_URL"]}">{c["hero"]["cta_secondary"]}</a>'
                    if articles_enabled
                    else ""
                ),
                "SERVICES_LABEL": c["services"]["label"],
                "SERVICES_TITLE": c["services"]["title"],
                "SERVICES_INTRO": c["services"]["intro"],
                "SERVICE_CARDS": "\n".join(service_cards),
                "NOTE_TITLE": c["services"]["note_title"],
                "NOTE": c["services"]["note"],
                "APPROACH_LABEL": c["approach"]["label"],
                "APPROACH_TITLE": c["approach"]["title"],
                "STEPS": "\n".join(steps),
                "ABOUT_LABEL": c["about"]["label"],
                "ABOUT_TITLE": c["about"]["title"],
                "ABOUT_BODY": c["about"]["body"],
                "CREDENTIALS_TITLE": c["about"]["credentials_title"],
                "CREDENTIALS": creds,
                "REGION_TITLE": c["about"]["region_title"],
                "REGION": c["about"]["region"],
                "CONTACT_LABEL": c["contact"]["label"],
                "CONTACT_TITLE": c["contact"]["title"],
                "CONTACT_DESC": c["contact"]["desc"],
                "EMAIL_LABEL": c["contact"]["email_label"],
                "GITHUB_LABEL": c["contact"]["github_label"],
                "OFFICE_LABEL": c["contact"]["office_label"],
                "OFFICE_VALUE": c["contact"]["office_value"],
                "CONTACT_CTA": c["contact"]["cta"],
            }
        )
        write_page(Path(lang_path) / "index.html", render(templates["home"], home_values))

        if not articles_enabled:
            continue

        # --- articles index ----------------------------------------------
        art_list_depth = home_depth + 1
        list_canonical = base_url + ("articles/" if lang == "en" else f"{lang}/articles/")
        other_list_canonical = base_url + ("zh-Hant/articles/" if lang == "en" else "articles/")
        common = common_values(c, art_list_depth, list_canonical, other_list_canonical)

        items = []
        for a in articles_by_lang[lang]:
            d = a["date"] or "—"
            items.append(
                f'''      <li>
        <p class="meta">{c["articles_page"]["published"]} {d}</p>
        <h2><a href="../articles/{a['slug']}/index.html">{escape(a["title"])}</a></h2>
        <p>{escape(a["description"])}</p>
      </li>'''
            )
        if items:
            list_html = f'<ul class="article-list">\n{chr(10).join(items)}\n    </ul>'
        else:
            list_html = f'<p class="section-intro">{c["articles_page"]["empty"]}</p>'

        list_values = dict(common)
        list_values.update(nav_fragments(c, common))
        list_values.update(
            {
                "TITLE": f'{c["articles_page"]["title"]} — xdo',
                "DESCRIPTION": c["articles_page"]["intro"],
                "BACK_HOME": c["articles_page"]["back"],
                "ARTICLES_LABEL": c["articles_page"]["label"],
                "ARTICLES_TITLE": c["articles_page"]["title"],
                "ARTICLES_INTRO": c["articles_page"]["intro"],
                "ARTICLE_LIST": list_html,
                "OTHER_PAGE_URL": other_page_url(lang, art_list_depth, "articles/index.html"),
            }
        )
        write_page(
            Path(lang_path) / "articles" / "index.html",
            render(templates["article_list"], list_values),
        )

        # --- article pages -------------------------------------------------
        for a in articles_by_lang[lang]:
            art_depth = home_depth + 2
            art_canonical = base_url + (
                f"articles/{a['slug']}/" if lang == "en" else f"{lang}/articles/{a['slug']}/"
            )
            other_art_canonical = base_url + (
                f"zh-Hant/articles/{a['slug']}/" if lang == "en" else f"articles/{a['slug']}/"
            )
            common = common_values(c, art_depth, art_canonical, other_art_canonical)
            art_values = dict(common)
            art_values.update(nav_fragments(c, common))
            other_lang_articles = articles_by_lang.get(c["other_lang_code"], [])
            if any(x["slug"] == a["slug"] for x in other_lang_articles):
                other_target = f"articles/{a['slug']}/index.html"
            else:
                other_target = "articles/index.html"
            art_values.update(
                {
                    "TITLE": f'{escape(a["title"])} — xdo',
                    "DESCRIPTION": escape(a["description"]) or c["description"],
                    "ARTICLE_DATE": f'{c["articles_page"]["published"]} {a["date"]}',
                    "ARTICLE_TITLE": escape(a["title"]),
                    "ARTICLE_BODY": a["body"],
                    "OTHER_PAGE_URL": other_page_url(lang, art_depth, other_target),
                }
            )
            write_page(
                Path(lang_path) / "articles" / a["slug"] / "index.html",
                render(templates["article"], art_values),
            )

    # --- shared static files -----------------------------------------------
    sitemap_urls = [base_url, base_url + "zh-Hant/"]
    if articles_enabled:
        sitemap_urls += [base_url + "articles/", base_url + "zh-Hant/articles/"]
    for lang in ("en", "zh-Hant"):
        prefix = "" if lang == "en" else f"{lang}/"
        for a in articles_by_lang[lang]:
            sitemap_urls.append(f"{base_url}{prefix}articles/{a['slug']}/")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in sitemap_urls:
        sitemap += f"  <url><loc>{url}</loc></url>\n"
    sitemap += "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    generated.append("sitemap.xml")

    (OUT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {base_url}sitemap.xml\n",
        encoding="utf-8",
    )
    generated.append("robots.txt")

    not_found = (
        '<!DOCTYPE html>\n<html lang="en" data-theme="light">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>404 — xdo</title>\n"
        # root-absolute paths: GitHub serves 404.html for missing URLs at any
        # depth, so relative asset paths would break on nested paths
        '<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">\n'
        '<link rel="stylesheet" href="/assets/style.css">\n'
        '<script>(function(){var t;try{t=localStorage.getItem("xdo-theme")}catch(e){}'
        'if(!t){t=window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}'
        'document.documentElement.setAttribute("data-theme",t)})();</script>\n</head>\n<body>\n'
        '<header class="site-header"><div class="wrap header-inner">'
        '<a class="brand" href="/index.html">'
        '<img class="logo logo-black" src="/assets/logo-black.png" alt="xdo" width="54" height="30">'
        '<img class="logo logo-white" src="/assets/logo-white.png" alt="xdo" width="54" height="30"></a></div></header>\n'
        '<main><div class="wrap"><p class="breadcrumb"><a href="/index.html">← xdo.dev</a></p>'
        '<h1 class="page-title">404</h1>'
        '<p class="section-intro">Page not found.</p></div></main>\n'
        '<script src="/assets/main.js"></script>\n</body>\n</html>\n'
    )
    (OUT / "404.html").write_text(not_found, encoding="utf-8")
    generated.append("404.html")

    # --- assets -------------------------------------------------------------
    assets_dir = ROOT / "assets"
    for f in sorted(assets_dir.glob("*")):
        if f.is_file():
            target = OUT / "assets" / f.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(f.read_bytes())
            generated.append(f"assets/{f.name}")
    # keep original brand files under assets/brand/
    for f in sorted((assets_dir / "brand").glob("*")):
        if f.is_file():
            target = OUT / "assets" / "brand" / f.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(f.read_bytes())
            generated.append(f"assets/brand/{f.name}")

    # --- manifest-based cleanup (Windows-safe) ------------------------------
    stale = []
    if MANIFEST.exists():
        try:
            old = set(json.loads(MANIFEST.read_text(encoding="utf-8")))
        except ValueError:
            old = set()
        for rel in sorted(old - set(generated)):
            p = OUT / rel
            if p.is_file():
                p.unlink()
                stale.append(rel)
            # prune now-empty directories (best effort)
            for parent in [p.parent] + list(p.parents):
                try:
                    if parent != OUT and parent.is_dir() and not any(parent.iterdir()):
                        parent.rmdir()
                except OSError:
                    break
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(sorted(generated), indent=2), encoding="utf-8")

    # --- report --------------------------------------------------------------
    total_drafts = {
        lang: len(load_articles(ROOT / "articles" / lang)) - len(articles_by_lang[lang])
        for lang in ("en", "zh-Hant")
    }
    print(f"Built {len(generated)} files into site/")
    print(f"  articles published: en={len(articles_by_lang['en'])}, zh-Hant={len(articles_by_lang['zh-Hant'])}")
    print(f"  drafts excluded:    en={total_drafts['en']}, zh-Hant={total_drafts['zh-Hant']}")
    if stale:
        print(f"  removed stale:      {', '.join(stale)}")

    # --- self-check ------------------------------------------------------------
    problems = []
    for rel in generated:
        if rel.endswith(".html"):
            html_text = (OUT / rel).read_text(encoding="utf-8")
            for src in re.findall(r'(?:href|src)="([^"]+)"', html_text):
                if src.startswith(("http:", "https:", "mailto:", "/")):
                    continue
                path_only = src.split("#")[0]
                if not path_only:
                    continue
                resolved = (OUT / rel).parent / path_only
                if not resolved.exists():
                    problems.append(f"{rel}: missing {src}")
    if problems:
        print("PROBLEMS FOUND:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("Self-check passed: all internal links and assets resolve.")


if __name__ == "__main__":
    build()
