#!/usr/bin/env python3
"""Fix legal-pages.json: extract real content from section.text (not breadcrumbs container)."""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path("/Users/andy/neoplus-rebuild")
RAW = ROOT / "raw" / "html"
BUILD = ROOT / "data" / "build"
BASE = "https://balashikha.neoplus-clinic.ru"

def txt(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else None

out = []
for p in json.loads((BUILD / "legal-pages.json").read_text()):
    slug = p["path"]
    f = RAW / (slug + ".html")
    s = BeautifulSoup(f.read_text(errors="replace"), "lxml")
    sec = s.select_one("section.text")
    blocks = []
    if sec:
        h1 = txt(sec.find("h1")) or p.get("h1")
        for el in sec.find_all(["p", "li", "h2", "h3"]):
            t = txt(el)
            if t and t != h1:
                blocks.append({"tag": el.name, "text": t})
        # dedupe keep order
        seen = set(); clean = []
        for b in blocks:
            if b["text"] in seen: continue
            seen.add(b["text"]); clean.append(b)
        out.append({"path": slug, "url": BASE + "/" + slug + "/", "title": p["title"],
                     "description": p["description"], "h1": h1, "blocks": clean})
    else:
        out.append({"path": slug, "url": BASE + "/" + slug + "/", "title": p["title"],
                     "description": p["description"], "h1": p.get("h1"), "blocks": []})

(BUILD / "legal-pages.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
for o in out:
    print(o["path"], "blocks:", len(o["blocks"]), "| text:", sum(len(b["text"]) for b in o["blocks"]))
