#!/usr/bin/env python3
"""
Builds the Hearthside Kitchen static website into the ../site folder.

1. Edit SETTINGS below (site name, domain, email, AdSense ID).
2. Optional: add photos as site/assets/img/recipes/<recipe-slug>.jpg
3. Run:  python3 tools/build.py
4. Commit and push to GitHub. Azure Static Web Apps publishes the /site folder.

Only Python 3.8+ is needed. No extra packages.
"""
import html
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content_recipes import CATEGORIES, RECIPES   # noqa: E402
from content_articles import ARTICLES              # noqa: E402

# ---------------------------------------------------------------------------
# SETTINGS — change these before you publish
# ---------------------------------------------------------------------------
SETTINGS = {
    "site_name": "Hearthside Kitchen",
    "tagline": "Comforting home cooking, made simple",
    "site_url": "https://www.yourdomain.com",          # no trailing slash
    "contact_email": "contact@yourdomain.com",
    "owner_name": "the Hearthside Kitchen team",
    "adsense_client": "",                              # e.g. "ca-pub-1234567890123456"
    "updated": date(2026, 11, 13),
    "featured_recipe": "easy-chicken-pot-pie",
    "popular_recipes": [
        "classic-meatloaf", "chicken-noodle-soup", "slow-cooker-beef-stew",
        "old-fashioned-apple-crisp", "baked-salmon-lemon-dill", "best-banana-bread",
    ],
}
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site")
S = SETTINGS
E = html.escape
UPDATED_HUMAN = f'{S["updated"].strftime("%B")} {S["updated"].day}, {S["updated"].year}'
UPDATED_ISO = S["updated"].isoformat()
PAGES = []
CAT = {c["slug"]: c for c in CATEGORIES}
REC = {r["slug"]: r for r in RECIPES}

LOGO = (
    '<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" fill="#b5452c"/>'
    '<path d="M14 30h36v6a14 14 0 0 1-14 14h-8a14 14 0 0 1-14-14z" fill="#fbf8f3"/>'
    '<rect x="10" y="27" width="44" height="5" rx="2.5" fill="#fbf8f3"/>'
    '<path d="M25 22c0-3 3-3 3-6M32 22c0-3 3-3 3-6M39 22c0-3 3-3 3-6" stroke="#fbf8f3" stroke-width="2.6" '
    'stroke-linecap="round" fill="none"/></svg>'
)
ICON_PRINT = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 14h12v7H6z"/></svg>'
ICON_SHARE = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>'
ICON_DOWN = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="M6 13l6 6 6-6"/></svg>'

NAV = [("Home", "index.html", "home"), ("Recipes", "recipes/index.html", "recipes"),
       ("Articles", "articles/index.html", "articles"), ("About", "about.html", "about"),
       ("Contact", "contact.html", "contact")]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def canonical_for(path):
    if path == "index.html":
        return S["site_url"] + "/"
    if path.endswith("/index.html"):
        return S["site_url"] + "/" + path[: -len("index.html")]
    return S["site_url"] + "/" + path


def prefix(path):
    return "../" * path.count("/")


def parse_qty(q):
    total = 0.0
    for part in q.split():
        if "/" in part:
            a, b = part.split("/")
            total += float(a) / float(b)
        else:
            total += float(part)
    return total


def fmt_minutes(m):
    if m < 60:
        return f"{m} min"
    h, r = divmod(m, 60)
    return f"{h} hr" + (f" {r} min" if r else "")


def iso_duration(m):
    h, r = divmod(m, 60)
    return "PT" + (f"{h}H" if h else "") + (f"{r}M" if r or not h else "")


def photo_for(slug):
    for ext in ("jpg", "jpeg", "webp", "png"):
        rel = f"assets/img/recipes/{slug}.{ext}"
        if os.path.exists(os.path.join(OUT, rel)):
            return rel
    return None


def tile(r, p, cls="tile", eager=False):
    photo = photo_for(r["slug"])
    if photo:
        loading = "eager" if eager else "lazy"
        return (f'<div class="{cls} tile-{r["category"]}"><img src="{p}{photo}" alt="{E(r["title"])}" '
                f'loading="{loading}" decoding="async" width="1200" height="750"></div>')
    return f'<div class="{cls} tile-{r["category"]}" aria-hidden="true">{r["emoji"]}</div>'


def total_minutes(r):
    return r["prep"] + r["cook"] + r.get("extra", 0)


def recipe_card(r, p):
    search = E(f'{r["title"]} {r["desc"]} {CAT[r["category"]]["name"]}'.lower())
    return (f'<a class="card" href="{p}recipes/{r["slug"]}.html" data-search="{search}">{tile(r, p)}'
            f'<div class="body"><span class="tag">{E(CAT[r["category"]]["name"])}</span>'
            f'<h3>{E(r["title"])}</h3><p>{E(r["desc"])}</p>'
            f'<span class="facts">{fmt_minutes(total_minutes(r))} · {r["servings"]} {E(r["yield_unit"])}</span></div></a>')


def article_card(a, p):
    return (f'<a class="card text-only" href="{p}articles/{a["slug"]}.html"><div class="body">'
            f'<span class="tag">Kitchen guide</span><h3>{E(a["title"])}</h3><p>{E(a["desc"])}</p>'
            f'<span class="facts">{a["minutes"]} min read</span></div></a>')


def breadcrumbs(items, p):
    lis = []
    for i, (label, href) in enumerate(items):
        if href and i < len(items) - 1:
            lis.append(f'<li><a href="{p}{href}">{E(label)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{E(label)}</li>')
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>'


def org():
    return {"@type": "Organization", "name": S["site_name"], "url": S["site_url"] + "/"}


def adsense_head():
    if S["adsense_client"]:
        return ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='
                + E(S["adsense_client"]) + '" crossorigin="anonymous"></script>')
    return "<!-- AdSense code goes here -->"


def layout(path, title, description, body, active=None, og_type="website", jsonld=None,
           noindex=False, body_class="", og_image=None):
    p = prefix(path)
    full_title = title if title == S["site_name"] else f"{title} | {S['site_name']}"
    canonical = canonical_for(path)
    cur = ' aria-current="page"'
    nav = "".join(f'<li><a href="{p}{h}"{cur if k == active else ""}>{E(l)}</a></li>' for l, h, k in NAV)
    lds = jsonld if isinstance(jsonld, list) else ([jsonld] if jsonld else [])
    ld = "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + "</script>" for x in lds)
    robots = "noindex" if noindex else "index, follow, max-image-preview:large"
    og_img = f'<meta property="og:image" content="{E(S["site_url"] + "/" + og_image)}">' if og_image else ""
    cat_links = "".join(f'<li><a href="{p}category/{c["slug"]}.html">{E(c["name"])}</a></li>' for c in CATEGORIES)
    page = f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(full_title)}</title>
<meta name="description" content="{E(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{E(canonical)}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{E(S['site_name'])}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:url" content="{E(canonical)}">
{og_img}
<meta name="twitter:card" content="summary_large_image">
<meta name="format-detection" content="telephone=no">
<meta name="theme-color" content="#fbf8f3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#171412" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-title" content="{E(S['site_name'])}">
<link rel="icon" href="{p}assets/img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{p}apple-touch-icon.png">
<link rel="manifest" href="{p}site.webmanifest">
<link rel="stylesheet" href="{p}assets/css/style.css">
<script>try{{var s=localStorage.getItem("hk-text-size");if(s==="1")document.documentElement.classList.add("text-lg");if(s==="2")document.documentElement.classList.add("text-xl");}}catch(e){{}}</script>
{adsense_head()}
{ld}
</head>
<body{f' class="{body_class}"' if body_class else ""}>
<a class="skip-link" href="#main">Skip to main content</a>
<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="{p}index.html">{LOGO}<span>{E(S['site_name'])}</span></a>
    <nav class="site-nav" aria-label="Main">
      <ul>{nav}<li><button type="button" class="text-size-btn" aria-label="Change text size"><span aria-hidden="true">A<span style="font-size:1.25em">A</span></span> Text size</button></li></ul>
    </nav>
  </div>
</header>
<main id="main">
<div class="container">
{body}
</div>
</main>
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h2>{E(S['site_name'])}</h2>
        <p>{E(S['tagline'])}. Tested home recipes with clear steps, everyday ingredients, and easy-to-read pages.</p>
      </div>
      <div>
        <h2>Recipes</h2>
        <ul>{cat_links}<li><a href="{p}recipes/index.html">All recipes</a></li></ul>
      </div>
      <div>
        <h2>Site Information</h2>
        <ul>
          <li><a href="{p}about.html">About Us</a></li>
          <li><a href="{p}contact.html">Contact Us</a></li>
          <li><a href="{p}privacy-policy.html">Privacy Policy</a></li>
          <li><a href="{p}terms-of-use.html">Terms of Use</a></li>
          <li><a href="{p}disclaimer.html">Disclaimer</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom"><p>&copy; <span id="year">{S['updated'].year}</span> {E(S['site_name'])}. All rights reserved.</p></div>
  </div>
</footer>
<script src="{p}assets/js/main.js" defer></script>
</body>
</html>
"""
    dest = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(page)


# ---------------------------------------------------------------------------
# Recipe pages
# ---------------------------------------------------------------------------
def build_recipes():
    for idx, r in enumerate(RECIPES):
        path = f"recipes/{r['slug']}.html"
        p = prefix(path)
        c = CAT[r["category"]]
        tot = total_minutes(r)

        facts = [("Prep", fmt_minutes(r["prep"]))]
        if r["cook"]:
            facts.append(("Cook", fmt_minutes(r["cook"])))
        if r.get("extra") and not r["cook"]:
            facts.append((r.get("extra_label", "Wait"), fmt_minutes(r["extra"])))
        facts.append(("Total", fmt_minutes(tot)))
        yield_txt = f'{r["servings"]} {r["yield_unit"]}'
        facts.append(("Makes" if r["yield_unit"] != "servings" else "Serves",
                      yield_txt if r["yield_unit"] != "servings" else str(r["servings"])))
        facts_html = "".join(f'<div class="fact"><span>{E(k)}</span><strong>{E(v)}</strong></div>' for k, v in facts)

        # Ingredients
        items, plain = [], []
        n = 0
        for q, text in r["ingredients"]:
            if q == "#":
                items.append(f'<li class="group">{E(text)}</li>')
                continue
            n += 1
            if q:
                qty = f'<span class="qty" data-qty="{parse_qty(q):.6g}">{E(q)}</span> '
                plain.append(f"{q} {text}")
            else:
                qty = ""
                plain.append(text)
            items.append(f'<li><label for="ing-{n}"><input type="checkbox" id="ing-{n}"><span>{qty}{E(text)}</span></label></li>')

        steps = "".join(f"<li>{E(s)}</li>" for s in r["steps"])
        tips = "".join(f"<li>{E(t)}</li>" for t in r["tips"])
        intro = "".join(f"<p>{E(x)}</p>" for x in r["intro"])
        yn = f' ({E(r["yield_note"])})' if r.get("yield_note") else ""

        same = [x for x in RECIPES if x["category"] == r["category"] and x["slug"] != r["slug"]]
        others = [x for x in RECIPES if x["category"] != r["category"]]
        related = (same + others[idx % len(others):] + others[:idx % len(others)])[:3]
        rel = "".join(recipe_card(x, p) for x in related)

        share_text = f'{r["title"]} — a recipe from {S["site_name"]}'
        body = f"""
<article class="recipe-page readable">
{breadcrumbs([("Home", "index.html"), ("Recipes", "recipes/index.html"), (c["name"], f"category/{c['slug']}.html"), (r["title"], None)], p)}
<h1>{E(r["title"])}</h1>
<p class="meta">By {E(S["owner_name"])} · Updated {UPDATED_HUMAN}</p>
<p class="lead">{E(r["desc"])}</p>
<div class="recipe-hero">{tile(r, p, eager=True)}</div>
<div class="quick-facts">{facts_html}</div>
<div class="action-row">
  <a class="btn btn-primary" href="#recipe">{ICON_DOWN} Jump to Recipe</a>
  <button type="button" class="btn btn-ghost" data-print>{ICON_PRINT} Print</button>
  <button type="button" class="btn btn-ghost" data-share="{E(share_text)}">{ICON_SHARE} Share</button>
</div>
<div class="intro">{intro}</div>

<section class="recipe-card" id="recipe" aria-labelledby="recipe-h">
  <h2 id="recipe-h">{E(r["title"])}</h2>
  <div class="recipe-tools">
    <div class="scaler">
      <span class="label">Batch size</span>
      <div class="seg" role="group" aria-label="Change batch size" data-scaler>
        <button type="button" data-scale="0.5" aria-pressed="false">Half</button>
        <button type="button" data-scale="1" aria-pressed="true">1×</button>
        <button type="button" data-scale="2" aria-pressed="false">2×</button>
      </div>
      <span class="servings-out"><span id="servings-count" data-base="{r["servings"]}">{r["servings"]}</span> {E(r["yield_unit"])}{yn if r["yield_unit"] == "servings" else ""}</span>
      <p class="scale-note">When you change the batch size, pan sizes and cooking times may need adjusting.</p>
    </div>
    <label class="cook-mode"><input type="checkbox" id="cook-mode"><span class="switch" aria-hidden="true"></span><span>Cook mode<small>Keeps your screen from going dark</small></span></label>
  </div>

  <h3>Ingredients</h3>
  <ul class="ingredients" data-key="{E(r["slug"])}">{"".join(items)}</ul>

  <h3>Instructions</h3>
  <ol class="steps">{steps}</ol>

  <h3>Tips for success</h3>
  <ul class="tips">{tips}</ul>

  <h3>Storing and reheating</h3>
  <div class="storage"><p>{E(r["storage"])}</p></div>
</section>
<p class="small-print">Always check ingredient labels for allergens. Cooking times are a guide; ovens vary. See our <a href="{p}disclaimer.html">disclaimer</a> for food safety and nutrition information.</p>
</article>
<section class="related no-print" aria-labelledby="rel-h"><h2 id="rel-h">You might also like</h2><div class="grid">{rel}</div></section>
"""
        photo = photo_for(r["slug"])
        ld = {
            "@context": "https://schema.org", "@type": "Recipe", "name": r["title"],
            "description": r["desc"], "author": org(), "publisher": org(),
            "datePublished": UPDATED_ISO, "dateModified": UPDATED_ISO,
            "prepTime": iso_duration(r["prep"]), "totalTime": iso_duration(tot),
            "recipeYield": [str(r["servings"]), f'{r["servings"]} {r["yield_unit"]}'],
            "recipeCategory": c["name"], "recipeCuisine": "American",
            "keywords": ", ".join([r["title"].lower(), "easy recipe", "home cooking", c["name"].lower()]),
            "recipeIngredient": plain,
            "recipeInstructions": [{"@type": "HowToStep", "position": i + 1, "text": s,
                                    "url": canonical_for(path) + "#recipe"} for i, s in enumerate(r["steps"])],
            "mainEntityOfPage": canonical_for(path),
        }
        if r["cook"]:
            ld["cookTime"] = iso_duration(r["cook"])
        if photo:
            ld["image"] = [S["site_url"] + "/" + photo]
        crumbs = {
            "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": S["site_url"] + "/"},
                {"@type": "ListItem", "position": 2, "name": c["name"], "item": canonical_for(f"category/{c['slug']}.html")},
                {"@type": "ListItem", "position": 3, "name": r["title"]},
            ]}
        layout(path, r["title"], r["desc"], body, active="recipes", og_type="article",
               jsonld=[ld, crumbs], og_image=photo)
        PAGES.append((path, "0.8"))


def build_categories():
    for c in CATEGORIES:
        path = f"category/{c['slug']}.html"
        p = prefix(path)
        recs = [r for r in RECIPES if r["category"] == c["slug"]]
        lead = ' class="lead"'
        intro = "".join(f'<p{lead if i == 0 else ""}>{E(x)}</p>' for i, x in enumerate(c["intro"]))
        others = "".join(f'<a class="cat-link" href="{o["slug"]}.html"><span class="em" aria-hidden="true">{o["emoji"]}</span>{E(o["name"])}</a>'
                         for o in CATEGORIES if o["slug"] != c["slug"])
        body = f"""
{breadcrumbs([("Home", "index.html"), ("Recipes", "recipes/index.html"), (c["name"], None)], p)}
<div class="readable">
<h1>{E(c["name"])} Recipes</h1>
{intro}
</div>
<div class="grid">{"".join(recipe_card(r, p) for r in recs)}</div>
<section class="related" aria-labelledby="more-h"><h2 id="more-h">More recipe categories</h2><div class="cat-grid">{others}</div></section>
"""
        ld = {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": canonical_for(f"recipes/{r['slug']}.html")} for i, r in enumerate(recs)]}
        layout(path, f'{c["name"]} Recipes', c["desc"], body, active="recipes", jsonld=ld)
        PAGES.append((path, "0.7"))


def build_recipes_index():
    path = "recipes/index.html"
    p = prefix(path)
    sections = []
    for c in CATEGORIES:
        recs = [r for r in RECIPES if r["category"] == c["slug"]]
        sections.append(f'<section data-cat-section aria-labelledby="c-{c["slug"]}"><div class="section-head">'
                        f'<h2 id="c-{c["slug"]}">{c["emoji"]} {E(c["name"])}</h2>'
                        f'<a href="{p}category/{c["slug"]}.html">See category →</a></div>'
                        f'<div class="grid">{"".join(recipe_card(r, p) for r in recs)}</div></section>')
    body = f"""
{breadcrumbs([("Home", "index.html"), ("Recipes", None)], p)}
<div class="readable">
<h1>All Recipes</h1>
<p class="lead">Classic, comforting recipes with clear steps and everyday ingredients. Every recipe can be halved or doubled with one tap.</p>
<div class="search" role="search">
  <label for="recipe-search">Search recipes</label>
  <input type="search" id="recipe-search" placeholder="Try “chicken” or “apple”" autocomplete="off" enterkeyhint="search">
</div>
<p class="no-results" id="no-results" hidden>No recipes match your search. Try a different word.</p>
</div>
{"".join(sections)}
"""
    layout(path, "All Recipes", "Browse easy, comforting recipes by category: breakfast, soups and stews, main dishes, side dishes, and desserts.", body, active="recipes")
    PAGES.append((path, "0.9"))


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------
def build_articles():
    for a in ARTICLES:
        path = f"articles/{a['slug']}.html"
        p = prefix(path)
        others = "".join(article_card(o, p) for o in ARTICLES if o["slug"] != a["slug"])
        body = f"""
<article class="prose">
{breadcrumbs([("Home", "index.html"), ("Articles", "articles/index.html"), (a["title"], None)], p)}
<h1>{E(a["title"])}</h1>
<p class="meta">By {E(S["owner_name"])} · Updated {UPDATED_HUMAN} · {a["minutes"]} min read</p>
{a["body"].replace("{p}", p)}
</article>
<section class="related no-print" aria-labelledby="rel-h"><h2 id="rel-h">More kitchen guides</h2><div class="grid">{others}</div></section>
"""
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["desc"],
              "datePublished": UPDATED_ISO, "dateModified": UPDATED_ISO, "author": org(), "publisher": org(),
              "mainEntityOfPage": canonical_for(path)}
        layout(path, a["title"], a["desc"], body, active="articles", og_type="article", jsonld=ld)
        PAGES.append((path, "0.7"))


def build_articles_index():
    path = "articles/index.html"
    p = prefix(path)
    body = f"""
{breadcrumbs([("Home", "index.html"), ("Articles", None)], p)}
<div class="readable"><h1>Kitchen Guides</h1>
<p class="lead">Practical, friendly advice to make home cooking easier, safer, and more enjoyable.</p></div>
<div class="grid">{"".join(article_card(a, p) for a in ARTICLES)}</div>
"""
    layout(path, "Kitchen Guides", "Helpful cooking guides: cooking for one or two, freezing meals safely, baking substitutions, and kitchen tools.", body, active="articles")
    PAGES.append((path, "0.7"))


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
def build_home():
    path = "index.html"
    p = ""
    f = REC[S["featured_recipe"]]
    cats = "".join(f'<a class="cat-link" href="category/{c["slug"]}.html"><span class="em" aria-hidden="true">{c["emoji"]}</span>{E(c["name"])}</a>' for c in CATEGORIES)
    popular = "".join(recipe_card(REC[s], p) for s in S["popular_recipes"])
    body = f"""
<section class="hero">
  <div>
    <p class="eyebrow">Easy home cooking</p>
    <h1>Comforting recipes, made simple</h1>
    <p class="lead">Classic American recipes with clear, step-by-step instructions, everyday ingredients, and easy-to-read pages. Cook for two or for the whole family with one tap.</p>
    <div class="actions">
      <a class="btn btn-primary" href="recipes/index.html">Browse all recipes</a>
      <a class="btn btn-ghost" href="articles/cooking-for-one-or-two.html">Cooking for two</a>
    </div>
  </div>
  <a class="hero-feature" href="recipes/{f["slug"]}.html">{tile(f, p, eager=True)}<div class="cap"><span class="eyebrow">This week’s favorite</span><strong>{E(f["title"])}</strong><span class="facts">{fmt_minutes(total_minutes(f))} · Serves {f["servings"]}</span></div></a>
</section>

<section aria-labelledby="cats-h">
  <h2 id="cats-h">What are you cooking today?</h2>
  <div class="cat-grid">{cats}</div>
</section>

<section aria-labelledby="pop-h">
  <div class="section-head"><h2 id="pop-h">Reader favorites</h2><a href="recipes/index.html">All recipes →</a></div>
  <div class="grid">{popular}</div>
</section>

<section aria-labelledby="guides-h">
  <div class="section-head"><h2 id="guides-h">Kitchen guides</h2><a href="articles/index.html">All guides →</a></div>
  <div class="grid">{"".join(article_card(a, p) for a in ARTICLES)}</div>
</section>

<section class="readable" aria-labelledby="welcome-h">
  <h2 id="welcome-h">Welcome to {E(S["site_name"])}</h2>
  <p>{E(S["site_name"])} is a collection of the comforting, dependable recipes that families have cooked for generations, from Sunday meatloaf and chicken pot pie to apple crisp and peach cobbler. Each recipe is written in plain language with clear steps, common grocery-store ingredients, and helpful tips for storing and reheating leftovers.</p>
  <p>Our pages are designed to be easy to use in the kitchen. Tap <strong>Cook mode</strong> to keep your phone screen awake while you cook, check off ingredients as you go, and use <strong>Text size</strong> at the top of any page to make the print larger.</p>
  <p><a href="about.html">Learn more about us</a> or <a href="contact.html">send us a note</a>.</p>
</section>
"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": S["site_name"], "url": S["site_url"] + "/",
          "description": S["tagline"], "publisher": org()}
    layout(path, S["site_name"], "Easy, comforting home recipes with clear steps and everyday ingredients: classic dinners, soups, sides, and old-fashioned desserts.", body, active="home", jsonld=ld)
    PAGES.append((path, "1.0"))


# ---------------------------------------------------------------------------
# Information and policy pages
# ---------------------------------------------------------------------------
def info_page(path, title, desc, inner, active=None, updated=True, priority="0.4"):
    p = prefix(path)
    upd = f'<p class="meta">Last updated: {UPDATED_HUMAN}</p>' if updated else ""
    body = f'<article class="prose">{breadcrumbs([("Home", "index.html"), (title, None)], p)}<h1>{E(title)}</h1>{upd}{inner}</article>'
    layout(path, title, desc, body, active=active)
    PAGES.append((path, priority))


def build_info_pages():
    name, url = E(S["site_name"]), E(S["site_url"])
    email = E(S["contact_email"])
    mail = f'<a href="mailto:{email}">{email}</a>'

    info_page("about.html", "About Us", f"Learn about {S['site_name']}, our recipes, and how we write and test them.", f"""
<p class="lead">{name} is a home for comforting, dependable recipes, the kind that bring people to the table.</p>
<h2>Our story</h2>
<p>Many of the best meals are the simple ones: a pot of soup on a cold day, a meatloaf on Sunday, a warm apple crisp shared with friends. We started {name} to collect these classic American dishes in one place and to write them the way a good friend would explain them in the kitchen, clearly, patiently, and without fuss.</p>
<h2>What makes our recipes different</h2>
<ul>
  <li><strong>Everyday ingredients.</strong> Our recipes use ingredients found in any American grocery store.</li>
  <li><strong>Clear, numbered steps.</strong> We explain not just what to do but how to tell when something is done.</li>
  <li><strong>Cooking for one, two, or a crowd.</strong> Every recipe can be halved or doubled with a single tap.</li>
  <li><strong>Helpful extras.</strong> Each recipe includes tips for success and instructions for storing, freezing, and reheating leftovers.</li>
  <li><strong>Food safety first.</strong> We include safe internal temperatures and follow USDA guidance in our storage advice.</li>
</ul>
<h2>Designed for easy reading</h2>
<p>We built {name} to be comfortable to use on a phone or tablet in the kitchen. The text is large and high-contrast, buttons are big and easy to tap, and you can make the text even larger with the <strong>Text size</strong> button. On recipe pages, <strong>Cook mode</strong> keeps your screen from going dark while you cook, and you can check off ingredients as you add them.</p>
<h2>Who we are</h2>
<p>{name} is written and maintained by {E(S['owner_name'])}, home cooks who believe a good meal is one of life’s simple pleasures. We test our recipes in ordinary home kitchens with ordinary equipment.</p>
<h2>Advertising</h2>
<p>To keep {name} free for everyone, we display advertisements from Google and other partners. Advertisers do not influence our recipes or articles. Read more in our <a href="privacy-policy.html">Privacy Policy</a>.</p>
<h2>Get in touch</h2>
<p>We love hearing from readers, especially about how a recipe turned out for you. Email us at {mail} or visit our <a href="contact.html">contact page</a>.</p>
""", active="about", updated=False, priority="0.5")

    info_page("contact.html", "Contact Us", f"Get in touch with {S['site_name']} with recipe questions, corrections, or feedback.", f"""
<p class="lead">Questions about a recipe? Suggestions for something new? We read every message.</p>
<div class="contact-card"><p><strong>Email us at:</strong></p><p class="email">{mail}</p><p>We aim to reply within two to three business days.</p></div>
<h2>How we can help</h2>
<ul>
  <li><strong>Recipe questions:</strong> Tell us which recipe you are making and what happened, and we will do our best to help.</li>
  <li><strong>Corrections:</strong> Spotted an error in an ingredient amount or a step? Please let us know the page and the details.</li>
  <li><strong>Recipe requests:</strong> Is there a family favorite you would like to see? We are always adding new recipes.</li>
  <li><strong>Accessibility:</strong> If anything on the site is hard to read or use, please tell us so we can improve it.</li>
  <li><strong>Privacy:</strong> For questions about your information, see our <a href="privacy-policy.html">Privacy Policy</a> or email us directly.</li>
</ul>
""", active="contact", updated=False, priority="0.5")

    info_page("privacy-policy.html", "Privacy Policy", f"How {S['site_name']} collects, uses, and protects information, including cookies and Google advertising.", f"""
<p>This Privacy Policy explains how {name} (“we,” “us,” or “our”) collects, uses, and protects information when you visit {url} (the “Site”). By using the Site, you agree to the practices described in this policy.</p>
<h2>Information we collect</h2>
<h3>Information you give us</h3>
<p>You do not need an account or any personal information to use this Site. If you email us, we receive your email address and whatever you include in your message, and we use it only to respond to you.</p>
<h3>Information collected automatically</h3>
<p>Our hosting provider (Microsoft Azure) automatically records standard technical information when you visit, such as your IP address, browser and device type, pages visited, and the date and time of your visit. This information is used to operate, secure, and improve the Site.</p>
<h3>Preferences stored on your device</h3>
<p>If you change the text size, the Site saves your choice in your browser’s local storage. Ingredients you check off on a recipe are saved in session storage until you close the tab. These preferences stay on your device and are not sent to us. Cook mode uses your browser’s Screen Wake Lock feature and does not collect any information.</p>
<h2>Cookies and similar technologies</h2>
<p>Cookies are small text files stored on your device. We and our partners may use cookies and similar technologies to remember preferences, understand how visitors use the Site, and deliver and measure advertising. You can control or delete cookies through your browser settings. On iPhone and iPad, go to <strong>Settings → Apps → Safari</strong> (or <strong>Settings → Safari</strong> on older versions) to manage cookies and website data.</p>
<h2>Advertising and Google AdSense</h2>
<p>We use Google AdSense and may work with other advertising partners to display ads on the Site. These partners may use cookies, web beacons, device identifiers, and similar technologies to collect information about your visits to this and other websites to provide relevant advertisements.</p>
<ul>
  <li>Third-party vendors, including Google, use cookies to serve ads based on your prior visits to this Site or other websites.</li>
  <li>Google’s use of advertising cookies enables it and its partners to serve ads to you based on your visits to this Site and/or other sites on the Internet.</li>
  <li>You may opt out of personalized advertising by visiting <a href="https://myadcenter.google.com/" rel="noopener">Google My Ad Center</a>.</li>
  <li>You can also opt out of some third-party vendors’ use of cookies for personalized advertising at <a href="https://www.aboutads.info/choices/" rel="noopener">www.aboutads.info/choices</a>.</li>
  <li>Learn more at <a href="https://policies.google.com/technologies/partner-sites" rel="noopener">How Google uses information from sites or apps that use its services</a>.</li>
</ul>
<h2>Analytics</h2>
<p>We may use analytics services, such as Google Analytics, to understand how visitors use the Site. These services may use cookies and collect information such as your IP address and browsing activity. You can opt out of Google Analytics with the <a href="https://tools.google.com/dlpage/gaoptout" rel="noopener">Google Analytics Opt-out Browser Add-on</a>.</p>
<h2>How we use information</h2>
<ul>
  <li>To operate, maintain, and improve the Site</li>
  <li>To respond to your messages</li>
  <li>To display and measure advertising that keeps the Site free</li>
  <li>To protect the Site against fraud, abuse, and security threats</li>
  <li>To comply with legal obligations</li>
</ul>
<p>We do not sell your personal information for money.</p>
<h2>Your privacy choices and rights</h2>
<p>Depending on where you live, including California, Virginia, Colorado, Connecticut, Texas, and other U.S. states with privacy laws, you may have the right to request access to, correction of, or deletion of personal information we hold about you, and to opt out of the use of your information for targeted advertising. Visitors in the European Economic Area, the United Kingdom, and Switzerland may have similar rights and will be asked for consent before personalized advertising cookies are used.</p>
<p>To make a request, email us at {mail}. You can also limit advertising cookies at any time using the links above, your browser settings, or a browser that supports the Global Privacy Control signal.</p>
<h2>Children’s privacy</h2>
<p>This Site is intended for a general adult audience and is not directed to children under 13. We do not knowingly collect personal information from children under 13. If you believe a child has provided us with personal information, please contact us and we will delete it.</p>
<h2>Links to other websites</h2>
<p>The Site may link to other websites. We are not responsible for their privacy practices and encourage you to read their privacy policies.</p>
<h2>Data security and retention</h2>
<p>We use reasonable safeguards, including secure HTTPS connections. No method of transmission or storage is completely secure. We keep email correspondence only as long as needed to respond and for reasonable record-keeping.</p>
<h2>Changes to this policy</h2>
<p>We may update this Privacy Policy from time to time. The “Last updated” date above shows when it was last revised.</p>
<h2>Contact us</h2>
<p>Questions about this Privacy Policy? Email us at {mail}.</p>
""", priority="0.3")

    info_page("terms-of-use.html", "Terms of Use", f"The terms and conditions for using the {S['site_name']} website.", f"""
<p>Welcome to {name}. By accessing or using {url} (the “Site”), you agree to these Terms of Use. If you do not agree, please do not use the Site.</p>
<h2>Use of the Site</h2>
<p>The Site provides recipes, cooking guides, and related content for personal, non-commercial use. You agree to use the Site only for lawful purposes and in a way that does not harm the Site or other users.</p>
<h2>Our content</h2>
<p>The recipe descriptions, instructions, tips, articles, design, and other original content on the Site are owned by {name} and protected by copyright. You are welcome to print recipes for your own personal use and to share links to our pages. Republishing our recipes, articles, or photos on other websites or in publications without written permission is not allowed.</p>
<h2>Prohibited activities</h2>
<ul>
  <li>Copying or scraping the Site’s content in bulk</li>
  <li>Attempting to interfere with the Site’s security or operation</li>
  <li>Using automated systems to generate artificial traffic or interact with advertisements</li>
  <li>Using the Site in any way that violates applicable law</li>
</ul>
<h2>Advertisements and third-party links</h2>
<p>The Site displays advertisements and may link to third-party websites. We do not control and are not responsible for third-party content, products, or services. Any dealings with advertisers are solely between you and the advertiser.</p>
<h2>Recipes and results</h2>
<p>Cooking results depend on ingredients, equipment, and technique, so your results may vary. You are responsible for safe food handling, for checking ingredients for allergens, and for making sure food is cooked to safe temperatures. Please read our <a href="disclaimer.html">Disclaimer</a>.</p>
<h2>Disclaimer of warranties</h2>
<p>The Site is provided “as is” and “as available.” We work hard to keep content accurate but make no warranties of any kind, express or implied, about its completeness, accuracy, reliability, or availability.</p>
<h2>Limitation of liability</h2>
<p>To the fullest extent permitted by law, {name} will not be liable for any indirect, incidental, special, or consequential damages arising from your use of, or inability to use, the Site.</p>
<h2>Changes to these terms</h2>
<p>We may update these Terms of Use from time to time. Continued use of the Site after changes are posted means you accept the updated terms.</p>
<h2>Contact</h2>
<p>Questions about these terms can be sent to {mail}.</p>
""", priority="0.3")

    info_page("disclaimer.html", "Disclaimer", f"Important information about recipes, food safety, allergies, and nutrition on {S['site_name']}.", f"""
<h2>General information</h2>
<p>The recipes, articles, and other content on {name} are provided for general informational and entertainment purposes. Cooking times, temperatures, and yields are guides; ovens, stovetops, and ingredients vary, so use your own judgment and check food for doneness.</p>
<h2>Food safety</h2>
<p>Always follow safe food-handling practices. Use a food thermometer to confirm that meat, poultry, seafood, and leftovers reach safe internal temperatures. For current guidance, visit the USDA Food Safety and Inspection Service at <a href="https://www.fsis.usda.gov/food-safety" rel="noopener">fsis.usda.gov</a>.</p>
<h2>Allergies and dietary needs</h2>
<p>Our recipes may contain or come into contact with common allergens, including milk, eggs, wheat, soy, peanuts, tree nuts, fish, shellfish, and sesame. Always read ingredient labels carefully. Product formulations can change.</p>
<h2>Not medical or nutrition advice</h2>
<p>Nothing on this Site is medical, dietary, or nutrition advice. If you follow a special diet for a health condition, such as a low-sodium, diabetic, or heart-healthy diet, or if you take medications that interact with certain foods, please talk with your doctor or a registered dietitian about which recipes and ingredients are right for you.</p>
<h2>Advertising</h2>
<p>This Site displays advertisements from Google AdSense and other partners. Ads are selected by those partners, not by us, and the appearance of an ad does not mean we endorse the advertiser, product, or service.</p>
<h2>External links</h2>
<p>Links to other websites are provided for convenience. We are not responsible for the content or practices of external sites.</p>
""", priority="0.3")


def build_404():
    path = "404.html"
    cats = "".join(f'<a class="cat-link" href="/category/{c["slug"]}.html"><span class="em" aria-hidden="true">{c["emoji"]}</span>{E(c["name"])}</a>' for c in CATEGORIES)
    body = f"""
<div class="readable"><h1>Page not found</h1>
<p class="lead">Sorry, we could not find that page. It may have moved, or the address may have a typo.</p>
<p><a class="btn btn-primary" href="/recipes/index.html">Browse all recipes</a></p>
<h2>Recipe categories</h2></div>
<div class="cat-grid">{cats}</div>
"""
    layout(path, "Page Not Found", "The page you were looking for could not be found.", body, noindex=True)
    f = os.path.join(OUT, path)
    with open(f, encoding="utf-8") as fh:
        txt = fh.read()
    txt = re.sub(r'(href|src)="(?!/|https?:|mailto:|#)([^"]+)"', r'\1="/\2"', txt)
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(txt)


# ---------------------------------------------------------------------------
# Supporting files
# ---------------------------------------------------------------------------
def build_support_files():
    urls = "".join(f"  <url><loc>{E(canonical_for(pth))}</loc><lastmod>{UPDATED_ISO}</lastmod><priority>{pri}</priority></url>\n" for pth, pri in PAGES)
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nDisallow: /404.html\n\nSitemap: {S['site_url']}/sitemap.xml\n")
    pub = S["adsense_client"].replace("ca-", "") if S["adsense_client"] else "pub-0000000000000000"
    note = "" if S["adsense_client"] else "# Replace pub-0000000000000000 with your AdSense publisher ID once approved.\n"
    with open(os.path.join(OUT, "ads.txt"), "w", encoding="utf-8") as f:
        f.write(f"{note}google.com, {pub}, DIRECT, f08c47fec0942fa0\n")
    manifest = {
        "name": S["site_name"], "short_name": S["site_name"], "start_url": "/", "display": "browser",
        "background_color": "#fbf8f3", "theme_color": "#b5452c",
        "icons": [{"src": "/assets/img/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }
    with open(os.path.join(OUT, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    with open(os.path.join(OUT, "assets/img/favicon.svg"), "w", encoding="utf-8") as f:
        f.write(LOGO.replace('<svg viewBox', '<svg xmlns="http://www.w3.org/2000/svg" viewBox').replace(' aria-hidden="true"', ""))


def main():
    build_home()
    build_recipes_index()
    build_categories()
    build_recipes()
    build_articles_index()
    build_articles()
    build_info_pages()
    build_404()
    build_support_files()
    photos = sum(1 for r in RECIPES if photo_for(r["slug"]))
    print(f"Built {len(PAGES) + 1} pages into {OUT}. Recipe photos found: {photos} of {len(RECIPES)}.")


if __name__ == "__main__":
    main()
