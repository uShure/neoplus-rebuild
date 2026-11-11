#!/usr/bin/env python3
"""Prepare clean build-ready JSON for the Astro site from crawled data."""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path("/Users/andy/neoplus-rebuild")
RAW = ROOT / "raw" / "html"
DATA = ROOT / "data"
BUILD = ROOT / "data" / "build"
BUILD.mkdir(parents=True, exist_ok=True)
BASE = "https://balashikha.neoplus-clinic.ru"

def txt(el):
    if el is None:
        return None
    t = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return t or None

def load(f):
    return BeautifulSoup(f.read_text(errors="replace"), "lxml")

def file_for_url(u):
    """Map site URL back to raw html file name."""
    path = u.replace(BASE, "").strip("/")
    if not path:
        return RAW / "index.html"
    if path.startswith("personal/"):
        return RAW / (path.replace("/", "__") + ".html")
    return RAW / (path.replace("/", "__") + ".html") if "__" in path else RAW / (path + ".html")

# canonical resolution for exact duplicates
canonical_map = {
    BASE + "/narkologicheskij-dispanser/": BASE + "/narkologicheskiy-dispanser/",
    BASE + "/reabilitatsiya-narkozavisimykh/": BASE + "/reabilitatsiya-narkozavisimyh/",
}

# ---------- structured content for every page ----------
def extract_sections(soup, skip_sections=("price", "faq", "doctors", "consultation", "departure", "rating-section", "reviews", "feedback", "advantages", "licences", "gallery", "video", "tour", "stocks", "intro", "intro-service", "cause")):
    """Text sections as markdown-ish blocks, excluding component sections rendered by templates."""
    ARTIFACTS = ("Я даю согласие", "Оставьте заявку и мы перезвоним", "Остались вопросы? Оставьте заявку",
                 "Нажимая на кнопку", "Согласие на получение сообщений")
    EMOJI = ["☎️", "📞", "📱", "⚕️", "💊", "💉", "🚑", "☎", "✅", "❗"]
    blocks = []
    for sec in soup.find_all("section"):
        classes = sec.get("class") or []
        first = classes[0] if classes else ""
        if first in skip_sections:
            continue
        h2 = sec.find("h2")
        parts = []
        if h2:
            parts.append(("h2", txt(h2)))
        for p in sec.find_all(["p", "li", "h3"]):
            if p.find_parent("table"):
                continue
            t = txt(p)
            if not t or any(a in t for a in ARTIFACTS) or t in [x[1] for x in parts]:
                continue
            for e in EMOJI:
                t = t.replace(e, "")
            t = re.sub(r"\s{2,}", " ", t).strip()
            if t:
                parts.append((p.name, t))
        if parts:
            blocks.append({"section": first, "heading": parts[0][1] if parts[0][0] == "h2" else None,
                           "items": [{"tag": tag, "text": text} for tag, text in parts]})
    return blocks

def faq_of(soup):
    out = []
    for it in soup.select(".faq__item"):
        q = txt(it.select_one(".faq__item-title, .hide-item__title"))
        a = txt(it.select_one(".hide-item__content"))
        if q:
            out.append({"q": q, "a": a})
    return out

pages = json.loads((DATA / "pages.json").read_text())
services = json.loads((DATA / "services.json").read_text())
prices_by_service = json.loads((DATA / "prices-by-service.json").read_text())

STATIC_PAGES = {"tseny", "otzyvy", "faq", "aktsii", "kontakty", "o-klinike-neoplus", "personal",
                "photogallery", "geography", "karta-sayta", "litsenzii", "kalkulyator",
                "narcologicheskaya-pomosch", "informatsiya-dlya-rodstvennikov"}
LEGAL_PREFIXES = ("politika", "soglasie", "soglashenie", "yuridiches")

service_pages = []
static_pages = []
legal_pages = []
doctor_pages = []

for rec in pages:
    u = rec["url"]
    path = u.replace(BASE, "").strip("/")
    f = file_for_url(u)
    if not f.exists():
        continue
    soup = load(f)
    meta = rec["meta"]
    entry = {
        "url": u,
        "path": path,
        "title": meta.get("title"),
        "description": meta.get("description"),
        "h1": rec["h1"],
        "canonical_override": canonical_map.get(u),
    }
    if path.startswith("personal/"):
        doctors_map = {d["url"]: d for d in json.loads((DATA / "doctors.json").read_text())}
        d = doctors_map.get(u)
        if d:
            entry["doctor"] = d
            doctor_pages.append(entry)
        continue
    if path in STATIC_PAGES:
        entry["sections"] = extract_sections(soup)
        entry["faq"] = faq_of(soup)
        static_pages.append(entry)
        continue
    if path.startswith(LEGAL_PREFIXES):
        body = txt(soup.select_one(".container"))
        entry["text"] = body
        legal_pages.append(entry)
        continue
    if path == "index" or not path:
        continue
    # service page
    entry["prices"] = prices_by_service.get(u, {}).get("items", [])
    entry["faq"] = next((s2.get("faq", []) for s2 in services if s2["url"] == u), [])
    entry["sections"] = extract_sections(soup)
    service_pages.append(entry)

# hero advantage strips (from intro-service section, small list of 3 facts)
for e in service_pages:
    f = file_for_url(e["url"])
    soup = load(f)
    intro = soup.select_one("section.intro-service")
    if intro:
        facts = [txt(li) for li in intro.select("li, .intro-service__item")]
        facts = [x for x in facts if x][:4]
        e["hero_facts"] = facts
        lead = None
        p = intro.find("p")
        if p:
            lead = txt(p)
        e["hero_lead"] = lead
        img = intro.select_one("img")
        if img:
            e["hero_img"] = "".join((img.get("src") or "").split())

(BUILD / "service-pages.json").write_text(json.dumps(service_pages, ensure_ascii=False, indent=1))
(BUILD / "static-pages.json").write_text(json.dumps(static_pages, ensure_ascii=False, indent=1))
(BUILD / "legal-pages.json").write_text(json.dumps(legal_pages, ensure_ascii=False, indent=1))
(BUILD / "doctor-pages.json").write_text(json.dumps(doctor_pages, ensure_ascii=False, indent=1))
print("services:", len(service_pages), "static:", len(static_pages), "legal:", len(legal_pages), "doctors:", len(doctor_pages))
