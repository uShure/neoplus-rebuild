#!/usr/bin/env python3
"""Post-build: doctor .html file URLs, robots.txt, sitemap.xml, redirects, server configs."""
import json
import shutil
from datetime import date
from pathlib import Path

ROOT = Path("/Users/andy/neoplus-rebuild")
DIST = ROOT / "site" / "dist"
SITE_ROOT = ROOT / "dist"
BASE = "https://balashikha.neoplus-clinic.ru"

# 1) doctor pages: dist/personal/<name>.html/index.html -> dist/personal/<name>.html
fixed = 0
for d in (DIST / "personal").glob("*.html"):
    if d.is_dir():
        inner = d / "index.html"
        if inner.exists():
            shutil.move(str(inner), str(d) + ".tmp")
            d.rmdir()
            Path(str(d) + ".tmp").rename(str(d))
            fixed += 1
print("doctor .html files fixed:", fixed)

services = json.loads((ROOT / "data/build/service-pages.json").read_text())
static_slugs = ["o-klinike-neoplus", "tseny", "personal", "aktsii", "otzyvy", "faq", "litsenzii",
                "kontakty", "photogallery", "geography", "karta-sayta", "kalkulyator",
                "narcologicheskaya-pomosch", "informatsiya-dlya-rodstvennikov"]
legal_slugs = [p["path"] for p in json.loads((ROOT / "data/build/legal-pages.json").read_text())]
doctor_urls = [d["url"] for d in json.loads((ROOT / "data/doctors.json").read_text())]

# 2) robots.txt (legal-info pages disallowed, как на старом сайте)
robots = """User-agent: *
Allow: /
Allow: /*.css
Allow: /*.js
Allow: /*.webp
Allow: /*.woff2
Disallow: /yuridicheskaya-informatsiya/
Disallow: /yuridicheskie-dokumenty/
Disallow: /send.php
Disallow: /*?*

Sitemap: https://balashikha.neoplus-clinic.ru/sitemap.xml
"""
(DIST / "robots.txt").write_text(robots)

# 3) sitemap.xml
today = date.today().isoformat()
urls = ["/"] + ["/" + s["path"] + "/" for s in services] + \
       ["/" + sl + "/" for sl in static_slugs] + \
       [d.replace(BASE, "") for d in doctor_urls] + \
       ["/" + sl + "/" for sl in legal_slugs if sl not in ("yuridicheskaya-informatsiya", "yuridicheskie-dokumenty")]
items = []
for u in urls:
    prio = "1.0" if u == "/" else ("0.8" if u.count("/") <= 2 else "0.6")
    items.append(
        "  <url><loc>" + BASE + u + "</loc><lastmod>" + today + "</lastmod><priority>" + prio + "</priority></url>"
    )
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(items) + "\n</urlset>\n"
(DIST / "sitemap.xml").write_text(sitemap)
print("sitemap urls:", len(urls))

# 4) redirects.csv + server configs (для склеенных дублей и будущих переездов)
exact_dups = [
    ("/narkologicheskij-dispanser/", "/narkologicheskiy-dispanser/", 301),
    ("/reabilitatsiya-narkozavisimykh/", "/reabilitatsiya-narkozavisimyh/", 301),
]
with open(ROOT / "redirects.csv", "w") as f:
    f.write("old_url,new_url,status_code\n")
    for old, new, code in exact_dups:
        f.write(f"{BASE}{old},{BASE}{new},{code}\n")

nginx = """# Нео+ Балашиха — редиректы склеенных дублей
# Вставить в server {} перед root/index
""" + "\n".join(
    f"rewrite ^{old.lstrip('/') if False else old[1:]}$ {new} permanent;" for old, new, _ in exact_dups
) + """

# trailing slash для каталогов (как на старом сайте)
location ~ ^(.+)/$ { try_files $1/index.html $1/ =404; }
error_page 404 /404.html;
"""
htaccess = """RewriteEngine On
""" + "\n".join(
    f"Redirect 301 {old} {new}" for old, new, _ in exact_dups
)
(ROOT / "nginx-redirects.conf").write_text(nginx)
(ROOT / ".htaccess").write_text(htaccess)

# 5) продублировать сборку в корневой /dist (ожидаемая структура результата)
if SITE_ROOT.exists():
    shutil.rmtree(SITE_ROOT)
shutil.copytree(DIST, SITE_ROOT)
n = sum(1 for _ in SITE_ROOT.rglob("*.html"))
print("root dist html files:", n)
print("DONE")
