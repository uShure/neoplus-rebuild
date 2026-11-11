#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Пересборка профилей врачей v2: точный маппинг h2/h3-подсекций старых страниц."""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path("/Users/andy/neoplus-rebuild")
RAW = ROOT / "raw" / "html"
DATA = ROOT / "site" / "src" / "data"
BASE = "https://balashikha.neoplus-clinic.ru"

# ключ (lowercase, без хвостового «:») → поле
SECTION_MAP = {
    "образование": "education",
    "образование и квалификация": "education",
    "образование и профессиональное развитие": "education",
    "профессиональный опыт": "experience",
    "опыт работы": "experience",
    "режим работы": "schedule",
    "сферы специализации": "specialization_detailed",
    "специализация врача": "specialization_short",
    "особый акцент в работе": "about",
    "образование и документы": "about",
    "о враче": "about",
    "почему стоит обратиться именно к врачу": "qa",
    "почему стоит обратиться": "qa",
    "когда нужна помощь психиатра-нарколога": "qa",
    "когда нужна помощь психотерапевта-сексолога": "qa",
    "когда нужна помощь психиатра-аддиктолога": "qa",
    "когда нужна помощь психотерапевта-токсиколога": "qa",
    "почему стоит доверять врачу": "qa",
    "почему стоит доверять специалисту": "qa",
    "контакты и запись на приём": None,
    "статьи автора": None,
    "отзывы о специалисте": None,
}
DAY_SPLIT = re.compile(r"(?=Понедельник|Вторник|Среда|Четверг|Пятница|Суббота|Воскресенье)")
SKIP_HEADINGS = ("образование и документы", "статьи автора")

def txt(el):
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else None

def parse_profile(url):
    slug = url.replace(BASE + "/personal/", "")
    f = RAW / ("personal__" + slug + ".html")
    s = BeautifulSoup(f.read_text(errors="replace"), "lxml")
    sec = s.select_one(".doctor-page") or s.body
    fields = {
        "education": [], "experience": [], "schedule": [],
        "specialization_short": [], "specialization_detailed": [],
        "about": [], "qa": [],
    }
    current = None
    qa_item = None
    for el in sec.find_all(["h2", "h3", "p", "li"], recursive=True):
        cls = " ".join(el.get("class") or [])
        # FAQ-блоки (hide-item) — вопросы врача
        if "hide-item" in cls or "faq__item" in cls:
            q = txt(el.select_one(".faq__item-title, .hide-item__title"))
            a = txt(el.select_one(".hide-item__content"))
            if q:
                fields["qa"].append({"q": q, "a": a})
            continue
        t = txt(el)
        if not t:
            continue
        if el.name in ("h2", "h3"):
            key = re.sub(r"[:\s]+$", "", t.lower().strip())
            # точные ключи + префиксные («почему стоит обратиться именно к <Имя>»)
            field = SECTION_MAP.get(key)
            if field is None:
                for k, v in SECTION_MAP.items():
                    if key.startswith(k):
                        field = v
                        break
            if field is None:
                if t.endswith("?"):
                    field = "qa"
                    qa_item = {"q": t, "a": ""}
                else:
                    field = None
            current = field
            if field == "qa":
                if qa_item is None or qa_item.get("q") != t:
                    qa_item = {"q": t, "a": ""}
                    fields["qa"].append(qa_item)
            continue
        # контент
        if t.lower().rstrip(":") in SKIP_HEADINGS:
            continue
        if current is None:
            continue
        if current == "qa":
            if qa_item is not None:
                qa_item["a"] = ((qa_item["a"] + " ") if qa_item["a"] else "") + t
            continue
        fields[current].append(t)
    # пост-обработка
    days = []
    for line in fields["schedule"]:
        for part in DAY_SPLIT.split(line):
            part = part.strip(" ;.")
            if part and re.match(r"^(Понедельник|Вторник|Среда|Четверг|Пятница|Суббота|Воскресенье)", part):
                days.append(part)
    fields["schedule"] = days or fields["schedule"]
    spec = []
    for line in fields["specialization_short"]:
        for part in re.split(r";", line):
            part = part.strip().rstrip(".").strip()
            if part:
                spec.append(part)
    fields["specialization_short"] = spec
    return fields

doctors = json.loads((DATA / "doctors.json").read_text())
for d in doctors:
    fields = parse_profile(d["url"])
    pr = d["profile"]
    pr["specialization_short"] = fields["specialization_short"]
    pr["specialization_detailed"] = fields["specialization_detailed"]
    pr["education"] = fields["education"]
    pr["experience"] = fields["experience"]
    pr["schedule"] = fields["schedule"]
    pr["about"] = " ".join(fields["about"]).strip() or None
    pr["qa"] = fields["qa"]
    for junk in ("specialization", "documents"):
        pr.pop(junk, None)
    print("="*12, d["name"])
    print("  short:", pr["specialization_short"])
    print("  detailed:", len(pr["specialization_detailed"]))
    print("  edu:", len(pr["education"]), "exp:", len(pr["experience"]), "sched:", len(pr["schedule"]), "qa:", len(pr["qa"]))
    print("  about:", (pr["about"] or "—")[:70])

(DATA / "doctors.json").write_text(json.dumps(doctors, ensure_ascii=False, indent=2))
print("doctors.json rewritten")
