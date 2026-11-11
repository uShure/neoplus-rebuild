#!/usr/bin/env python3
"""Extract structured content from crawled HTML into /data/*.json."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

ROOT = Path("/Users/andy/neoplus-rebuild")
RAW_HTML = ROOT / "raw" / "html"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
BASE = "https://balashikha.neoplus-clinic.ru"

def url_for_file(f):
    """Reconstruct site URL from the saved slug file name."""
    stem = f.stem
    if stem == "index":
        return BASE + "/"
    if "__" in stem:
        # personal__name.html.html -> /personal/name.html
        parts = stem.split("__")
        rest = "__".join(parts[1:])
        return f"{BASE}/{parts[0]}/{rest}"
    return f"{BASE}/{stem}/"

def load(f):
    return BeautifulSoup(f.read_text(errors="replace"), "lxml")

def txt(el):
    if el is None:
        return None
    t = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
    return t or None

def clean_spaces(u):
    return "".join(u.split()) if u else u

def meta_of(soup):
    m = {}
    t = soup.find("title")
    m["title"] = txt(t)
    for name in ["description", "keywords", "robots"]:
        el = soup.find("meta", attrs={"name": name})
        if el:
            m[name] = el.get("content", "").strip()
    for prop in ["og:title", "og:description", "og:image", "og:type", "og:url", "og:site_name"]:
        el = soup.find("meta", attrs={"property": prop})
        if el:
            m[prop] = el.get("content", "").strip()
    can = soup.find("link", rel="canonical")
    if can:
        m["canonical"] = can.get("href")
    return m

def breadcrumbs_of(soup):
    out = []
    nav = soup.select_one(".breadcrumbs")
    if not nav:
        return out
    for li in nav.find_all("li"):
        a = li.find("a")
        if a:
            out.append({"title": txt(a), "url": clean_spaces(a.get("href", ""))})
        else:
            sp = li.find("span")
            if sp:
                out.append({"title": txt(sp), "url": None})
    return out

def prices_from_table(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = [txt(c) for c in tr.find_all(["td", "th"])]
        cells = [c for c in cells if c]
        if not cells:
            continue
        name = cells[0]
        price = next((c for c in cells[1:] if re.search(r"\d", c) and c != "Заказать"), None)
        rows.append({"name": name, "price": price})
    return rows

def faq_from_soup(soup, scope=None):
    items = []
    root = scope or soup
    for it in root.select(".faq__item, .faq-page__item"):
        q = txt(it.select_one(".faq__item-title, .hide-item__title"))
        a_el = it.select_one(".hide-item__content")
        a = txt(a_el)
        if q:
            items.append({"q": q, "a": a})
    return items

def reviews_from_soup(soup):
    out = []
    for it in soup.select(".reviews-page__item, .reviews__item"):
        name = txt(it.select_one(".reviews__info span"))
        age = txt(it.select_one(".reviews__info p"))
        body = txt(it.select_one(".reviews__text"))
        img = it.select_one(".reviews__picture img")
        src_icon = it.select_one(".reviews__review-from img")
        date = txt(it.select_one(".reviews__date, .review__date"))
        if body:
            out.append({
                "author": name, "age": age, "text": body,
                "avatar": img.get("src") if img else None,
                "source_icon": src_icon.get("src") if src_icon else None,
                "date": date,
            })
    return out

pages = sorted(RAW_HTML.glob("*.html"))
pages_index = []
for f in pages:
    soup = load(f)
    url = url_for_file(f)
    h1 = soup.find("h1")
    h2s = [txt(h) for h in soup.find_all("h2")]
    h3s = [txt(h) for h in soup.find_all("h3")]
    rec = {
        "url": url,
        "slug": url.split("//", 1)[1].split("/", 1)[1].rstrip("/") if "/" in url.split("/", 2)[-1] else "",
        "file": f.name,
        "meta": meta_of(soup),
        "h1": txt(h1),
        "h2": h2s,
        "h3": h3s,
        "breadcrumbs": breadcrumbs_of(soup),
        "sections": [cls for s in soup.find_all("section") for cls in [(" ".join(s.get("class") or [])).strip()]],
    }
    pages_index.append(rec)
(DATA / "pages.json").write_text(json.dumps(pages_index, ensure_ascii=False, indent=2))

# ---------- PRICES (from /tseny/ + per-service price sections) ----------
soup_t = load(RAW_HTML / "tseny.html")
price_groups = []
h2s = soup_t.find_all("h2")
tables = soup_t.find_all("table")
for h2, table in zip(h2s, tables):
    price_groups.append({"group": txt(h2), "items": prices_from_table(table)})
(DATA / "prices.json").write_text(json.dumps({
    "source": BASE + "/tseny/",
    "groups": price_groups,
}, ensure_ascii=False, indent=2))

# per-service price tables
service_prices = {}
for f in pages:
    soup = load(f)
    url = url_for_file(f)
    sec = soup.select_one("section.price")
    if not sec:
        continue
    title = None
    h2 = sec.find("h2")
    if h2:
        title = txt(h2)
    rows = []
    for table in sec.find_all("table"):
        rows += prices_from_table(table)
    if rows:
        service_prices[url] = {"title": title, "items": rows}
(DATA / "prices-by-service.json").write_text(json.dumps(service_prices, ensure_ascii=False, indent=2))

# ---------- DOCTORS ----------
doctors = []
plist = RAW_HTML / "personal.html"
soup_p = load(plist)
for a in soup_p.select("a.doctors-page__item, a.doctors__item"):
    href = clean_spaces(a.get("href", ""))
    name = txt(a.select_one(".doctors__bottom p"))
    spec = txt(a.select_one(".doctors__bottom span"))
    img = a.select_one("img")
    doctors.append({
        "name": name, "specialty": spec, "url": BASE + href if href.startswith("/") else href,
        "photo": img.get("src") if img else None,
    })
for d in doctors:
    slug = d["url"].replace(BASE + "/", "").replace("/", "__")
    f = RAW_HTML / (slug + ".html")
    if not f.exists():
        f = RAW_HTML / (slug + ".html.html")
    if not f.exists():
        continue
    soup_d = load(f)
    sec = soup_d.select_one(".doctor-page") or soup_d
    sections = {}
    for h2 in sec.find_all("h2"):
        key = txt(h2)
        # collect following sibling content until next h2
        parts = []
        for sib in h2.find_next_siblings():
            if sib.name in ("h2", "h1"):
                break
            t = txt(sib)
            if t:
                parts.append(t)
        sections[key] = parts
    photo = soup_d.select_one(".doctor-page img, .doctors__picture img")
    d["profile"] = {
        "url": d["url"],
        "meta": meta_of(soup_d),
        "h1": txt(soup_d.find("h1")),
        "education": sections.get("Образование:", []),
        "experience": sections.get("Опыт работы", []),
        "schedule": sections.get("Режим работы:", []),
        "specialization": sections.get("Специализация врача:", []),
        "documents": sections.get("Образование и документы:", []),
        "photo_page": photo.get("src") if photo else None,
        "diploma_images": [i.get("src") for i in soup_d.find_all("img") if "diplom" in (i.get("src") or "").lower()],
    }
(DATA / "doctors.json").write_text(json.dumps(doctors, ensure_ascii=False, indent=2))

# ---------- REVIEWS ----------
soup_r = load(RAW_HTML / "otzyvy.html")
reviews = reviews_from_soup(soup_r)
(DATA / "reviews.json").write_text(json.dumps({
    "source": BASE + "/otzyvy/",
    "count": len(reviews),
    "items": reviews,
}, ensure_ascii=False, indent=2))

# ---------- PROMOS ----------
soup_a = load(RAW_HTML / "aktsii.html")
promos = []
for it in soup_a.select(".stocks-page__item, .stocks__item"):
    title = txt(it.select_one(".stocks-page__title, .current-title, .stocks__name"))
    text = txt(it.select_one(".stocks-page__descr, .stocks__text, .stocks-page__text"))
    img = it.select_one(".stocks-page__picture img")
    promos.append({"title": title, "text": text, "image": img.get("src") if img else None})
(DATA / "promos.json").write_text(json.dumps({
    "source": BASE + "/aktsii/",
    "count": len(promos),
    "items": promos,
}, ensure_ascii=False, indent=2))

# ---------- CONTACTS ----------
soup_c = load(RAW_HTML / "kontakty.html")
contacts_text = txt(soup_c.select_one(".contacts-page")) or txt(soup_c.body)
footer_soup = load(RAW_HTML / "index.html")
footer = footer_soup.find("footer")
phones = sorted(set(re.findall(r"\+7[\s\(]*\d{3}[\)\s]*[\d\s\-]{7,12}", contacts_text + " " + txt(footer or ""))))
emails = sorted(set(re.findall(r"[\w.\-]+@[\w.\-]+", contacts_text + " " + txt(footer or ""))))
contacts = {
    "phones": phones,
    "emails": emails,
    "address_contact_center": "г. Балашиха, улица Советская, 47",
    "legal_entity": "ООО «НЕО ПЛЮС»",
    "inn": "6670512492",
    "ogrn": "1226600076185",
    "license_main": {
        "number": "Л041-01021-66/01009753",
        "date": "28.12.2023",
        "address": "620033, Свердловская область, г Екатеринбург, ул Норильская, стр. 77",
    },
    "license_stacionar_partner": {
        "entity": "ООО «Югэкосервис+»",
        "number": "Л041-01050-61/00347983",
        "date": "28.12.2021",
        "address": "г. Ростов-на-Дону, ул. Красноармейская, 170",
    },
    "raw_page_text": contacts_text,
}
(DATA / "contacts.json").write_text(json.dumps(contacts, ensure_ascii=False, indent=2))

# ---------- LEGAL ----------
legal = {
    "licenses_images": [i.get("src") for i in (load(RAW_HTML / "litsenzii.html").select(".licences-page img")) if i.get("src") and "home.svg" not in i.get("src")],
    "documents": [],
    "pages": {},
}
soup_y = load(RAW_HTML / "yuridicheskaya-informatsiya.html")
legal["pages"]["yuridicheskaya-informatsiya"] = {"url": BASE + "/yuridicheskaya-informatsiya/", "text": txt(soup_y.select_one(".container"))}
soup_yd = load(RAW_HTML / "yuridicheskie-dokumenty.html")
legal["pages"]["yuridicheskie-dokumenty"] = {"url": BASE + "/yuridicheskie-dokumenty/", "text": txt(soup_yd.select_one(".container"))}
for a in soup_yd.find_all("a", href=True):
    href = clean_spaces(a["href"])
    if any(href.lower().endswith(e) for e in (".pdf", ".jpg", ".png", ".doc", ".docx")):
        legal["documents"].append({"title": txt(a), "url": BASE + href if href.startswith("/") else href})
for slug_, label in [("politika-konfidentsialnosti", "politika-konfidentsialnosti"),
                     ("politika-v-otnoshenii-obrabotki-i-zaschity-personalnyh-dannyh", "politika-pd"),
                     ("soglashenie-ob-ispolzovanii-sayta", "soglashenie-sayta"),
                     ("soglasie-na-obrabotku-personalnyh-dannyh", "soglasie-pd"),
                     ("soglasie-na-obrabotku-personalnyh-dannyh-yandeksmetrikoi", "soglasie-ym"),
                     ("soglasie-na-poluchenie-informatsionnyh-i-reklamnyh-soobscheniy", "soglasie-reklama")]:
    f = RAW_HTML / (slug_ + ".html")
    if f.exists():
        s_ = load(f)
        legal["pages"][label] = {"url": f"{BASE}/{slug_}/", "text": txt(s_.select_one(".container"))}
(DATA / "legal.json").write_text(json.dumps(legal, ensure_ascii=False, indent=2))

# ---------- FAQ (dedicated page) ----------
soup_f = load(RAW_HTML / "faq.html")
faq_groups = []
current_group = None
for el in soup_f.select_one(".faq-page").descendants:
    pass
# simpler: walk h2 + faq items
inner = soup_f.select_one(".faq-page")
groups = []
h2 = inner.find_all("h2")
# split by h2 order: items appear after each h2
all_nodes = inner.select(".faq__item")
group_titles = [txt(h) for h in h2]
# assign items to groups by DOM order
container = inner
cursor = 0
gi = -1
for child in container.find_all(["h2", "div"]):
    if child.name == "h2":
        gi += 1
        groups.append({"group": txt(child), "items": []})
    cls = child.get("class") or []
    if "faq__item" in cls and gi >= 0:
        q = txt(child.select_one(".faq__item-title, .hide-item__title"))
        a = txt(child.select_one(".hide-item__content"))
        if q:
            groups[gi]["items"].append({"q": q, "a": a})
(DATA / "faq.json").write_text(json.dumps({"source": BASE + "/faq/", "groups": groups}, ensure_ascii=False, indent=2))

# ---------- WIDGETS ----------
html_index = (RAW_HTML / "index.html").read_text(errors="replace")
widgets = {
    "yandex_metrika_id": "66047221",
    "bitrix24_portal": "b3713987",
    "bitrix24_call_tracker": "https://cdn-ru.bitrix24.ru/b3713987/crm/tag/call.tracker.js?27860243",
    "form_endpoints": {
        "main_lead": "/send.php",
        "review_submit": "/add_otzyv.php",
        "ajax_request": "/netcat_template/ajax/request.php",
        "hash_check": "/netcat_template/ajax/hash-check.php",
    },
    "form_fields": ["catalogue", "BitrixID", "city", "type", "cc", "sub", "mes", "urlMessage", "title_url_message", "params[phone][]", "params[adConsent][]"],
    "consent_checkbox": "params[adConsent][]",
    "other_scripts": ["/send.js", "/redisign/assets/js/request.js", "/vefovi/ln.js", "https://news.google.com/swg/js/v1/publisher.js", "sourcebuster.min.js"],
    "map": "google.com/maps link on contacts page",
}
(DATA / "widgets.json").write_text(json.dumps(widgets, ensure_ascii=False, indent=2))

# ---------- SERVICES (grouping) ----------
services = []
for rec in pages_index:
    u = rec["url"]
    path = urlsplit(u).path.strip("/")
    if not path or path in ("tseny", "otzyvy", "faq", "aktsii", "kontakty", "o-klinike-neoplus", "personal",
                            "photogallery", "geography", "karta-sayta", "litsenzii", "kalkulyator") or path.startswith("personal/") \
       or path.startswith(("politika", "soglasie", "soglashenie", "yuridiches")):
        continue
    price_info = service_prices.get(u)
    services.append({
        "url": u,
        "h1": rec["h1"],
        "meta": rec["meta"],
        "has_price_table": bool(price_info),
        "price_items_count": len(price_info["items"]) if price_info else 0,
        "faq": faq_from_soup(load(RAW_HTML / rec["file"])),
    })
(DATA / "services.json").write_text(json.dumps(services, ensure_ascii=False, indent=2))

print("DONE")
for j in sorted(DATA.glob("*.json")):
    print(" ", j.name, f"{j.stat().st_size/1024:.1f} KB")
