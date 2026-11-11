#!/usr/bin/env python3
"""NeoPlus Balashikha site crawler — saves raw HTML of every page on the subdomain."""
import concurrent.futures as cf
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
import urllib.request
import urllib.error
import ssl

ROOT = Path("/Users/andy/neoplus-rebuild")
RAW = ROOT / "raw" / "html"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://balashikha.neoplus-clinic.ru"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) ZCode/3.18.0 Chrome/152.0.7977.130 Electron/44.7.0 Safari/537.36")

def load_cookies():
    pairs = []
    for line in (ROOT / "raw" / "cookies.txt").read_text().splitlines():
        line = line.strip()
        if line and "=" in line:
            k, v = line.split("=", 1)
            pairs.append(f"{k}={v}")
    return "; ".join(pairs)

COOKIES = load_cookies()
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

CHALLENGE_MARK = "gorizontal-vertikal"

def fetch(url, timeout=40):
    from urllib.parse import quote
    s = urlsplit(url)
    safe = quote(s.path, safe="/%()") + (("?" + s.query) if s.query else "")
    req = urllib.request.Request(urlunsplit((s.scheme, s.netloc, safe, "", "")), headers={
        "User-Agent": UA,
        "Cookie": COOKIES,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
        "Referer": BASE + "/",
    })
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.status, r.read().decode("utf-8", errors="replace")

def is_challenge(html):
    return CHALLENGE_MARK in html[:4000]

def slug_for(url):
    p = urlsplit(url).path
    p = p.strip("/")
    if not p:
        return "index"
    return p.replace("/", "__") or "index"

def allowed(url):
    path = urlsplit(url).path
    for d in ("/amp/", "/testovaya-stranitsa/", "/heavy/", "/zayavka/", "/ajax/",
              "/search/", "/fetch/", "/connectors/", "/test/"):
        if path.startswith(d):
            return False
    return True

def norm(url, base_url):
    url = "".join(url.split())  # site emits malformed hrefs with stray spaces
    u = urljoin(base_url, url)
    s = urlsplit(u)
    if s.scheme not in ("http", "https"):
        return None
    if s.netloc != "balashikha.neoplus-clinic.ru":
        return None
    u = urlunsplit((s.scheme, s.netloc, s.path, "", ""))  # drop query+frag
    if not u.endswith("/") and not re.search(r"\.[a-z0-9]{2,5}$", u.split("/")[-1], re.I):
        u += "/"
    return u

A_HREF = re.compile(r'<a[^>]+href=["\']([^"\']+)["\']', re.I)

ASSET_EXT = re.compile(r"\.(jpe?g|png|gif|webp|svg|ico|pdf|mp4|webm|woff2?|ttf|otf|css|js|json|xml)(\?.*)?$", re.I)

def main():
    seed = set()
    sm = (ROOT / "raw" / "sitemap.xml").read_text()
    for loc in re.findall(r"<loc>([^<]+)</loc>", sm):
        u = norm(loc.strip(), BASE + "/")
        if u:
            seed.add(u)
    # robots-disallowed but owned legal pages (Andy's own site, required for the new footer)
    for extra in ("/yuridicheskaya-informatsiya/", "/yuridicheskie-dokumenty/",
                  "/politika-konfidencialnosti/", "/politika-konfidencialnnosti/"):
        seed.add(BASE + extra)
    seen, results, failed = set(), {}, {}
    todo = sorted(u for u in seed if allowed(u))
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        pending = {}
        def submit(url):
            if url in pending.values() or url in results or url in failed:
                return
            seen.add(url)
            fut = ex.submit(fetch, url)
            pending[fut] = url
        for u in todo:
            submit(u)
        while pending:
            fut = next(cf.as_completed(list(pending)))
            url = pending.pop(fut)
            try:
                status, body = fut.result()
            except urllib.error.HTTPError as e:
                failed[url] = {"status": e.code, "error": str(e)}
                print(f"FAIL {e.code} {url}")
                continue
            except Exception as e:
                failed[url] = {"status": None, "error": repr(e)}
                print(f"ERR  {url}: {e!r}")
                continue
            if is_challenge(body):
                failed[url] = {"status": status, "error": "challenge"}
                print(f"CHLG {url}")
                continue
            if ASSET_EXT.search(url):
                with open(ROOT / "raw" / "asset-urls.txt", "a") as f:
                    f.write(url + "\n")
                print(f"ASST {status} {url}")
            else:
                html = body
                path = RAW / (slug_for(url) + ".html")
                path.write_text(html)
                results[url] = {"file": str(path), "bytes": len(html)}
                print(f"OK   {status} {url} ({len(html)}b)")
                for href in A_HREF.findall(html):
                    nu = norm(href, url)
                    if nu and nu not in seen:
                        submit(nu)
            time.sleep(0.1)
    (ROOT / "raw" / "crawl-manifest.json").write_text(json.dumps({
        "fetched": results, "failed": failed, "seeds_from_sitemap": sorted(seed),
    }, ensure_ascii=False, indent=2))
    print(f"\nDONE pages={len(results)} assets={sum(1 for _ in open(ROOT/'raw'/'asset-urls.txt')) if (ROOT/'raw'/'asset-urls.txt').exists() else 0} failed={len(failed)}")

if __name__ == "__main__":
    main()
