#!/usr/bin/env python3
"""Extract per-page main content as markdown into data/content/ (keeps all visible text incl. hidden tabs/FAQ)."""
import re
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path("/Users/andy/neoplus-rebuild")
RAW_HTML = ROOT / "raw" / "html"
OUT = ROOT / "data" / "content"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://balashikha.neoplus-clinic.ru"

MAIN_SELECTORS = [
    "section.intro-service", "section.intro", "section.price", "section.text",
    "section.faq", "section.doctors", "section.why", "section.facts",
    "section.advantages", "section.departure", "section.rating-section",
    "section.reviews", "section.feedback", "section.consultation",
    "section.licences", "section.gallery", "section.video", "section.tour",
    "section.stocks", "section.cause",
    "section.price-page", "section.faq-page", "section.reviews-page",
    "section.stocks-page", "section.doctors-page", "section.licences-page",
    "section.gallery-page", "section.contacts-page", "section.contacts",
    "section.doctor-page", "section[class*=text]",
]

def slug_for(f):
    stem = f.stem
    if stem == "index":
        return "index"
    if "__" in stem:
        parts = stem.split("__")
        return parts[0] + "/" + "__".join(parts[1:])
    return stem

def el_to_md(el):
    out = []
    for child in el.children:
        if isinstance(child, NavigableString):
            t = re.sub(r"\s+", " ", str(child)).strip()
            if t:
                out.append(t + " ")
        elif isinstance(child, Tag):
            name = child.name
            if name in ("h1", "h2", "h3", "h4"):
                out.append("\n\n" + "#" * int(name[1]) + " " + re.sub(r"\s+", " ", child.get_text(" ", strip=True)) + "\n\n")
            elif name == "p":
                t = re.sub(r"\s+", " ", child.get_text(" ", strip=True))
                if t:
                    out.append("\n" + t + "\n")
            elif name in ("ul", "ol"):
                for li in child.find_all("li", recursive=False):
                    t = re.sub(r"\s+", " ", li.get_text(" ", strip=True))
                    if t:
                        out.append(("- " if name == "ul" else "1. ") + t + "\n")
                out.append("\n")
            elif name == "table":
                rows = child.find_all("tr")
                out.append("\n| Услуга | Цена |\n|---|---|\n")
                for tr in rows:
                    cells = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
                    cells = [c for c in cells if c and c != "Заказать"]
                    if cells:
                        out.append("| " + " | ".join(cells[:2]) + " |\n")
                out.append("\n")
            elif name == "img":
                src = child.get("src") or child.get("data-src")
                alt = child.get("alt", "")
                if src and not src.endswith(".svg"):
                    out.append(f"\n![{alt}]({src})\n")
            elif name in ("div", "section", "article", "span", "picture", "source", "a", "strong", "b", "em", "br", "button"):
                if name in ("a",):
                    href = child.get("href", "")
                    t = re.sub(r"\s+", " ", child.get_text(" ", strip=True))
                    if t and href.startswith(("http", "/", "tel:", "mailto:")):
                        out.append(f"[{t}]({href}) ")
                    else:
                        out.append(el_to_md(child))
                elif name in ("strong", "b", "em"):
                    t = re.sub(r"\s+", " ", child.get_text(" ", strip=True))
                    if t:
                        out.append(t + " ")
                else:
                    out.append(el_to_md(child))
    return "".join(out)

for f in sorted(RAW_HTML.glob("*.html")):
    soup = BeautifulSoup(f.read_text(errors="replace"), "lxml")
    slug = slug_for(f)
    md = [f"# SOURCE: {BASE}/{'' if slug == 'index' else slug + '/'}\n"]
    title = soup.find("title")
    if title:
        tt = re.sub(r"\s+", " ", title.get_text(strip=True))
        md.append(f"title: {tt}\n\n")
    h1 = soup.find("h1")
    if h1:
        h1t = re.sub(r"\s+", " ", h1.get_text(" ", strip=True))
        md.append(f"# {h1t}\n\n")
    sections = []
    for sel in MAIN_SELECTORS:
        sections.extend(soup.select(sel))
    # dedupe by id(), preserve DOM order
    seen = set()
    ordered = []
    for s in sections:
        if id(s) not in seen:
            seen.add(id(s))
            ordered.append(s)
    body_html = soup.find("body")
    used = "\n".join(el_to_md(s) for s in ordered)
    md.append(used)
    text = "".join(md)
    text = re.sub(r"\n{3,}", "\n\n", text)
    dest = OUT / (slug.replace("/", "__") + ".md")
    dest.write_text(text.strip() + "\n")

print("content files:", len(list(OUT.glob('*.md'))))
