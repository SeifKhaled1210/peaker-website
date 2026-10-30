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

PAGES = {"home": "/", "services": "/services/", "work": "/work/", "odoo": "/odoo/", "about": "/about/", "contact": "/contact/"}

# ---------------------------------------------------------------- graphics
# The chevron base of the Peaker mark (100 x 80 grid, every angle 45 degrees).
BASE = "M0 80 L50 30 L100 80 L84 80 L50 46 L16 80 Z"
SUPERGRAPHIC = f'<svg class="supergraphic" viewBox="0 30 100 50" aria-hidden="true" focusable="false"><path fill="currentColor" d="{BASE}"/></svg>'
MARKER = '<svg class="marker" viewBox="0 0 14 7" aria-hidden="true" focusable="false"><path fill="currentColor" d="M7 0L14 7H0Z"/></svg>'
ICON_CHAT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5 5.3 15A8 8 0 1 1 9 18.7Z"/><path d="M9 11h.01M12 11h.01M15 11h.01" stroke-linecap="round" stroke-width="2.6"/></svg>'
ICON_MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>'
ICON_PHONE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2Z"/></svg>'


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
                      founder_name=site[f"founder_name_{lang}"], founder_bio=site[f"founder_bio_{lang}"])
        meta_key = {"home": "home", "services": "services_page", "work": "work_page", "odoo": "odoo_page", "about": "about_page", "contact": "contact_page"}
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
    css = DIST / "assets" / "css" / "styles.css"
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
