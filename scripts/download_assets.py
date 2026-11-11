#!/usr/bin/env python3
"""Download all assets referenced by crawled pages into assets/original (path-preserving) + url-map.json."""
import concurrent.futures as cf
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import urllib.request
import urllib.error
import ssl

from bs4 import BeautifulSoup

ROOT = Path("/Users/andy/neoplus-rebuild")
RAW_HTML = ROOT / "raw" / "html"
ASSETS = ROOT / "assets" / "original"
ASSETS.mkdir(parents=True, exist_ok=True)
BASE = "https://balashikha.neoplus-clinic.ru"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) ZCode/3.18.0 Chrome/152.0.7977.130 Electron/44.7.0 Safari/537.36")
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

def load_cookies():
    pairs = []
    for line in (ROOT / "raw" / "cookies.txt").read_text().splitlines():
        line = line.strip()
        if line and "=" in line:
            k, v = line.split("=", 1)
            pairs.append(f"{k}={v}")
    return "; ".join(pairs)

COOKIES = load_cookies()
ASSET_EXT = re.compile(r"\.(jpe?g|png|gif|webp|svg|ico|bmp|avif|pdf|mp4|webm|mp3|woff2?|ttf|otf|eot)(\?|$)", re.I)

def fetch_bytes(url):
    from urllib.parse import quote
    s = urlsplit(url)
    path = quote(unquote(s.path), safe="/%()")
    req = urllib.request.Request(
        urlunsplit := f"{s.scheme}://{s.netloc}{path}" + (f"?{s.query}" if s.query else ""),
        headers={"User-Agent": UA, "Cookie": COOKIES, "Referer": BASE + "/"})
    with urllib.request.urlopen(req, timeout=120, context=CTX) as r:
        return r.read()

def local_path_for(url):
    s = urlsplit(url)
    path = unquote(s.path).lstrip("/")
    if not path:
        path = "index"
    return ASSETS / path

def collect_urls():
    urls = set()
    for f in RAW_HTML.glob("*.html"):
        html = f.read_text(errors="replace")
        soup = BeautifulSoup(html, "lxml")
        for tag, attr in [("img", "src"), ("img", "data-src"), ("source", "src"),
                          ("link", "href"), ("script", "src"), ("video", "src"),
                          ("video", "poster")]:
            for el in soup.find_all(tag):
                v = el.get(attr)
                if v:
                    urls.add(urljoin(BASE + "/", v.strip()))
        for el in soup.find_all("img", srcset=True):
            for part in el["srcset"].split(","):
                u = part.strip().split(" ")[0]
                if u:
                    urls.add(urljoin(BASE + "/", u))
        for meta in soup.find_all("meta"):
            if meta.get("property") in ("og:image", "twitter:image") and meta.get("content"):
                urls.add(urljoin(BASE + "/", meta["content"].strip()))
        for a in soup.find_all("a", href=True):
            h = "".join(a["href"].split())
            if ASSET_EXT.search(h):
                urls.add(urljoin(BASE + "/", h))
        # inline styles url(...)
        for m in re.findall(r"url\((['\"]?)([^)'\"]+)\1\)", html):
            urls.add(urljoin(BASE + "/", m[1].strip()))
    return {u for u in urls if urlsplit(u).netloc == "balashikha.neoplus-clinic.ru" and ASSET_EXT.search(u)}

def main():
    urls = sorted(collect_urls())
    print(f"asset URLs to download: {len(urls)}")
    urlmap, failed = {}, []
    def work(u):
        lp = local_path_for(u)
        try:
            if lp.exists() and lp.stat().st_size > 0:
                return u, "cached"
            lp.parent.mkdir(parents=True, exist_ok=True)
            data = fetch_bytes(u)
            lp.write_bytes(data)
            return u, len(data)
        except urllib.error.HTTPError as e:
            return u, f"HTTP {e.code}"
        except Exception as e:
            return u, repr(e)[:120]
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for u, res in ex.map(work, urls):
            if isinstance(res, str):
                failed.append({"url": u, "error": res})
                print("FAIL", res, u)
            else:
                urlmap[u] = str(local_path_for(u).relative_to(ROOT))
                print("OK", res, u.rsplit("/", 1)[-1][:60])
            time.sleep(0.05)
    # CSS files: also mine their url() references
    css_files = [p for p in ASSETS.rglob("*.css")]
    extra = set()
    for cf_ in css_files:
        try:
            css = cf_.read_text(errors="replace")
        except Exception:
            continue
        for m in re.findall(r"url\((['\"]?)([^)'\"]+)\1\)", css):
            u = urljoin(BASE + "/", m[1].strip())
            if urlsplit(u).netloc == "balashikha.neoplus-clinic.ru" and ASSET_EXT.search(u):
                extra.add(u)
    print(f"extra refs from CSS: {len(extra)}")
    for u in sorted(extra - set(urlmap)):
        u_, res = work(u)
        if isinstance(res, str):
            failed.append({"url": u, "error": res}); print("FAIL", res, u)
        else:
            urlmap[u] = str(local_path_for(u).relative_to(ROOT)); print("OK", res, u.rsplit("/", 1)[-1][:60])
    (ROOT / "assets" / "url-map.json").write_text(json.dumps(
        {"map": urlmap, "failed": failed}, ensure_ascii=False, indent=2))
    print(f"\nDONE downloaded={len(urlmap)} failed={len(failed)}")

if __name__ == "__main__":
    main()
