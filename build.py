#!/usr/bin/env python3
"""Build the Peaker website into ./dist

Usage:   pip install jinja2      (once)
         python3 build.py
         python3 build.py --base /repo-name --preview   (GitHub Pages preview)

Edit text in src/content/en.json and src/content/ar.json,
contact details in src/site.json, then run the build again.
"""
import argparse, json, re, shutil, time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"
VERSION = time.strftime("%Y%m%d%H%M")

site = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
content = {l: json.loads((SRC / "content" / f"{l}.json").read_text(encoding="utf-8")) for l in ("en", "ar")}
for _c in content.values():   # flat list of every service, used by forms and links
    _c["services"] = [dict(s, cat=cat["id"]) for cat in _c["categories"] for s in cat["services"]]

PAGES = {"home": "/", "services": "/services/", "work": "/work/", "partner": "/partnership/", "odoo": "/odoo/", "about": "/about/", "contact": "/contact/"}

# ---------------------------------------------------------------- graphics
# The chevron base of the Peaker mark (100 x 80 grid, every angle 45 degrees).
BASE = "M0 80 L50 30 L100 80 L84 80 L50 46 L16 80 Z"
SUPERGRAPHIC = f'<svg class="supergraphic" viewBox="0 30 100 50" aria-hidden="true" focusable="false"><path fill="currentColor" d="{BASE}"/></svg>'
MARKER = '<svg class="marker" viewBox="0 0 14 7" aria-hidden="true" focusable="false"><path fill="currentColor" d="M7 0L14 7H0Z"/></svg>'
ICON_CHAT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5 5.3 15A8 8 0 1 1 9 18.7Z"/><path d="M9 11h.01M12 11h.01M15 11h.01" stroke-linecap="round" stroke-width="2.6"/></svg>'
ICON_MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>'
ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2Z"/></svg>'


def _i(d, sw="1.8"):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{d}</svg>'

ICONS = {
    "development": _i('<path d="m8 7-5 5 5 5M16 7l5 5-5 5M13.5 4l-3 16"/>'),
    "marketing": _i('<path d="M3 10v4h4l7 4V6l-7 4H3Z"/><path d="M17.5 9a4 4 0 0 1 0 6"/>'),
    "web-development": _i('<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M6.5 6.5h.01M9 6.5h.01"/>'),
    "erp": _i('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'),
    "crm": _i('<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.3-5.5 6.5-5.5s5.7 2 6.5 5.5"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18.5 14.8c1.6.8 2.6 2.5 3 5.2"/>'),
    "apps": _i('<rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M10.5 18.5h3"/>'),
    "integrations": _i('<path d="M4 9h14l-3.5-3.5M20 15H6l3.5 3.5"/>'),
    "account-management": _i('<path d="M4 5h16v11H8l-4 4V5Z"/><path d="M8 9.5h8M8 12.5h5"/>'),
    "content-creation": _i('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m10 9.5 4.5 2.5-4.5 2.5v-5Z"/>'),
    "paid-media": _i('<path d="M4 19V5M4 19h16"/><path d="m7 15 4-4 3 3 5-6"/>'),
    "strategy": _i('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>'),
    "branding": _i('<path d="m12 3 7 7-7 11-7-11 7-7Z"/><circle cx="12" cy="11" r="2"/>'),
    "handshake": _i('<path d="m11 7-2.5-2.5L3 10l5 5"/><path d="m13 7 2.5-2.5L21 10l-7.5 7.5a1.8 1.8 0 0 1-2.5 0L8 14.5"/><path d="m11 7 3 3m-4.5 1.5 2.5 2.5m-4.5-.5 2 2"/>'),
    "card": _i('<rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="M2.5 10h19M6 15h4"/>'),
    "arrow": _i('<path d="M5 12h14M13 6l6 6-6 6"/>', "2.2").replace('<svg ', '<svg class="arrow" ', 1),
    "x": _i('<path d="M6 6l12 12M18 6 6 18"/>', "2.6"),
    "check": _i('<path d="m5 12.5 4.5 4.5L19 7.5"/>', "2.6"),
    "bolt": _i('<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"/>', "2"),
    "play": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 4.5v15l13-7.5-13-7.5Z"/></svg>',
    "globe": _i('<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3Z"/>', "2"),
    "target": _i('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>', "2"),
    "eye": _i('<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>', "2"),
    "chat": ICON_CHAT, "mail": ICON_MAIL, "phone": ICON_PHONE,
}

BENTO = {
    # development: big photo, two singles, wide, full-width
    "web-development": {"cls": "span-2 row-2 photo", "img": "lumen-analytics.webp"},
    "apps": {"cls": "span-2"},
    "integrations": {"cls": "span-4 wide"},
    # marketing: same rhythm
    "paid-media": {"cls": "span-2 row-2"},
    "strategy": {"cls": "span-2"},
    "branding": {"cls": "span-4 wide"},
}


def chevron(cx, a, half=170, t=40):
    return (f'<path d="M{cx-half} {a+half} L{cx} {a} L{cx+half} {a+half} L{cx+half-t} {a+half} '
            f'L{cx} {a+t} L{cx-half+t} {a+half} Z"/>')

CLIMB = chevron(200, 200) + chevron(200, 130) + chevron(200, 60) + '<path class="peak" d="M200 0 L240 40 L160 40 Z"/>'

AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def with_counts(items):
    """Add count-up data to results like '30+' or '+٧٬٠٠٠'; others stay static."""
    out = []
    for r in items:
        r = dict(r)
        raw = r["num"].translate(AR_DIGITS)
        m = re.fullmatch(r"([+]?)([0-9][0-9,٬]*)([+]?)", raw)
        if m:
            r["count"] = int(re.sub(r"[,٬]", "", m.group(2)))
            r["pre"], r["suf"] = m.group(1), m.group(3)
        out.append(r)
    return out


def stack_svg(c):
    """The hero graphic: four chevron layers rising to the orange peak."""
    rtl = c["dir"] == "rtl"
    cx = 390 if rtl else 150
    sign = -1 if rtl else 1
    anchor = "start"  # direction is inherited, so "start" is the right edge in Arabic
    s = c["stack"]
    layers = [(300, s["l1"], 1), (244, s["l2"], 2), (188, s["l3"], 3), (132, s["l4"], 4)]
    out = [f'<svg class="stack" viewBox="0 0 540 440" role="img" aria-label="{s["label"]}">']
    for a, label, i in layers:
        pts = f"{cx-120},{a+120} {cx},{a} {cx+120},{a+120} {cx+98},{a+120} {cx},{a+22} {cx-98},{a+120}"
        tx = cx + sign * 146
        ty = a + 120 - 4
        out.append(
            f'<g class="rise d{i}"><polygon class="layer layer-{i}" points="{pts}"/>'
            f'<line class="tick" x1="{cx + sign*126}" y1="{ty-6}" x2="{cx + sign*138}" y2="{ty-6}"/>'
            f'<text x="{tx}" y="{ty}" text-anchor="{anchor}">{label}</text></g>')
    out.append(
        f'<g class="rise d5"><polygon class="peak" points="{cx},40 {cx+56},96 {cx-56},96"/>'
        f'<text class="peak-label" x="{cx + sign*74}" y="80" text-anchor="{anchor}">{s["peak"]}</text></g>')
    out.append("</svg>")
    return "".join(out)


def jsonld():
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Peaker",
        "alternateName": "بيكر",
        "url": site["domain"],
        "logo": site["domain"] + "/assets/img/mark.svg",
        "email": site["email"],
        "telephone": site["phone_link"],
        "slogan": "From foundation to peak.",
        "address": {"@type": "PostalAddress", "addressLocality": "Cairo", "addressCountry": "EG"},
        "areaServed": ["EG", "SA", "AE", "KW", "QA", "BH", "OM"],
        "sameAs": [u for u in (site["linkedin"], site["instagram"], site["facebook"]) if u],
    }, ensure_ascii=False)


def rebase(text, base):
    """Prefix root-relative links with the site's base path (for GitHub Pages project sites)."""
    if not base:
        return text
    text = re.sub(r'((?:href|src|action)=")/(?!/)', r'\1' + base + '/', text)
    return text.replace('url("/assets/', f'url("{base}/assets/')


def build(base="", preview=False):
    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SRC / "assets", DIST / "assets")
    for f in (SRC / "root").iterdir():
        shutil.copy(f, DIST / f.name)
    shutil.copytree(SRC / "static", DIST, dirs_exist_ok=True)   # demo pages etc.

    env = Environment(loader=FileSystemLoader(SRC / "templates"), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    count = 0
    for lang, c in content.items():
        prefix = "" if lang == "en" else "/ar"
        shared = dict(c=c, s=site, prefix=prefix, version=VERSION, supergraphic=SUPERGRAPHIC, marker=MARKER,
                      icon_chat=ICON_CHAT, icon_mail=ICON_MAIL, icon_phone=ICON_PHONE, stack=stack_svg(c), jsonld=jsonld(),
                      ic=ICONS, bento=BENTO, climb_paths=CLIMB,
                      work_items=with_counts(c["home"]["work_items"]), gc_results=with_counts(c["work_page"]["gc"]["results"]),
                      founder_name=site[f"founder_name_{lang}"], founder_bio=site[f"founder_bio_{lang}"],
                      founder_initials="".join(w[0] for w in site["founder_name_en"].split()[:2]) if site["founder_name_en"] else "")
        meta_key = {"home": "home", "services": "services_page", "work": "work_page", "partner": "partner", "odoo": "odoo_page", "about": "about_page", "contact": "contact_page"}
        for page, url in PAGES.items():
            m = c[meta_key[page]]
            path = prefix + url
            ctx = dict(shared, page=page, path=path, en_path=url, ar_path="/ar" + url,
                       alt_path=("/ar" + url) if lang == "en" else url,
                       meta={"title": m["title"], "description": m["description"]})
            html = rebase(env.get_template(f"{page}.html").render(**ctx), base)
            if preview:
                html = html.replace("<head>", '<head>\n<meta name="robots" content="noindex">', 1)
            out = DIST / path.lstrip("/") / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html, encoding="utf-8")
            count += 1
        nf = env.get_template("404.html").render(**dict(shared, page="404", path=prefix + "/404.html", en_path="/", ar_path="/ar/",
                                                         alt_path="/ar/" if lang == "en" else "/",
                                                         meta={"title": c["notfound"]["title"], "description": c["notfound"]["text"]}))
        nf = rebase(nf, base)
        (DIST / (prefix.lstrip("/") + "/404.html").lstrip("/")).write_text(nf, encoding="utf-8")

    # sitemap, robots, manifest
    today = time.strftime("%Y-%m-%d")
    urls = []
    for url in PAGES.values():
        for lang_path in (url, "/ar" + url):
            urls.append(
                f'  <url><loc>{site["domain"]}{lang_path}</loc><lastmod>{today}</lastmod>'
                f'<xhtml:link rel="alternate" hreflang="en" href="{site["domain"]}{url}"/>'
                f'<xhtml:link rel="alternate" hreflang="ar" href="{site["domain"]}/ar{url}"/></url>')
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {site['domain']}/sitemap.xml\n", encoding="utf-8")
    (DIST / "site.webmanifest").write_text(json.dumps({
        "name": "Peaker", "short_name": "Peaker", "start_url": f"{base}/", "display": "standalone",
        "background_color": "#FFFFFF", "theme_color": "#0F1B3D",
        "icons": [{"src": f"{base}/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": f"{base}/icon-512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2), encoding="utf-8")
    css = DIST / "assets" / "css" / "v2.css"
    css.write_text(rebase(css.read_text(encoding="utf-8"), base), encoding="utf-8")
    if preview:
        (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
        (DIST / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {count} pages + 2 error pages into {DIST}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="", help='path the site lives under, e.g. "/peaker-website"')
    ap.add_argument("--preview", action="store_true", help="hide from search engines (for test sites)")
    a = ap.parse_args()
    build(a.base.rstrip("/"), a.preview)
