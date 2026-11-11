#!/usr/bin/env python3
"""Patch pass: fix per-service price rows (multi-column tables) and hero facts/lead/price."""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path("/Users/andy/neoplus-rebuild")
RAW = ROOT / "raw" / "html"
BUILD = ROOT / "data" / "build"
BASE = "https://balashikha.neoplus-clinic.ru"

def txt(el):
    if el is None:
        return None
    t = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return t or None

def load(u):
    path = u.replace(BASE, "").strip("/")
    f = RAW / (path + ".html")
    return BeautifulSoup(f.read_text(errors="replace"), "lxml")

PRICE_RE = re.compile(r"(от\s*)?[\d\s\u00a0]{2,}(\s*(₽|руб))", re.I)

def parse_table(table):
    header = [txt(c) for c in table.select("tr th")] or None
    rows = []
    for tr in table.select("tr"):
        cells = [txt(c) for c in tr.select("td")]
        cells = [c for c in cells if c]
        if not cells:
            continue
        if len(cells) == 1:
            continue
        name = cells[0]
        price = cells[-1] if PRICE_RE.search(cells[-1]) else None
        row = {"name": name, "price": price}
        if len(cells) >= 4:
            row["desc"] = cells[1]
            row["term"] = cells[-2] if not PRICE_RE.search(cells[-2]) else None
        elif len(cells) == 2 and not price:
            row["desc"] = cells[1]
        rows.append(row)
    return header, rows

sp = json.loads((BUILD / "service-pages.json").read_text())
for e in sp:
    soup = load(e["url"])
    sec = soup.select_one("section.price")
    rows, header = [], None
    if sec:
        for t in sec.select("table"):
            h, r = parse_table(t)
            header = header or h
            rows += r
    e["price_header"] = header
    e["prices"] = rows
    # hero facts
    intro = soup.select_one("section.intro-service")
    if intro:
        e["hero_facts"] = [txt(x) for x in intro.select(".intro-service__advantages-text") if txt(x)]
        e["hero_lead"] = txt(intro.select_one(".intro-service__text"))
        e["hero_price"] = txt(intro.select_one(".intro-service-price"))
        e["hero_sub"] = txt(intro.select_one(".intro-service__subtitle"))
        img = intro.select_one("picture img")
        e["hero_img"] = img.get("src") if img else None
        # breadcrumbs2 category (parent direction)
        bc = intro.select("ul li a")
        e["direction"] = txt(bc[-1]) if bc else None

(BUILD / "service-pages.json").write_text(json.dumps(sp, ensure_ascii=False, indent=1))
ok = sum(1 for e in sp if e["prices"] and all(r["price"] for r in e["prices"][:3]))
print("services:", len(sp), "| with clean prices:", ok)
sample = next(e for e in sp if e["path"] == "vyvod-iz-zapoya")
print("header:", sample["price_header"])
print("row1:", sample["prices"][1])
print("hero:", sample["hero_facts"], "|", (sample["hero_lead"] or "")[:60], "|", sample["hero_price"], "|", sample["direction"])
