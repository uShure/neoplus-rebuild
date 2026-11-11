#!/usr/bin/env python3
"""Optimize images for the new site: heroes, doctors, gallery, licenses, review avatars, misc."""
import json
import re
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path("/Users/andy/neoplus-rebuild")
SRC = ROOT / "assets" / "original"
OUT = ROOT / "site" / "public" / "img"
OUT.mkdir(parents=True, exist_ok=True)

def save_webp(src: Path, dest: Path, max_w: int, quality: int = 72):
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        im = Image.open(src)
        im = im.convert("RGB") if im.mode not in ("RGB", "L") else im
        if im.width > max_w:
            h = round(im.height * max_w / im.width)
            im = im.resize((max_w, h), Image.LANCZOS)
        im.save(dest, "WEBP", quality=quality, method=6)
        return dest.stat().st_size
    except Exception as e:
        print("FAIL", src.name, repr(e)[:80])
        return 0

def local(url_path: str) -> Path:
    from urllib.parse import unquote
    return SRC / unquote(url_path.lstrip("/"))

report = {}

# 1) service heroes 1600w
heroes = sorted((SRC / "imgs" / "services").glob("*head.webp"))
total = 0
for h in heroes:
    n = save_webp(h, OUT / "heroes" / h.name, 1600, 68)
    total += n
report["heroes"] = (len(heroes), round(total / 1024 / 1024, 1))
# a few service heroes live under other names (banner_toxikomaniya etc.) — handled by same folder scan
# 2) doctors 640w
docs = sorted((SRC / "imgs" / "doctors").glob("*.webp"))
for d in docs:
    save_webp(d, OUT / "doctors" / d.name, 640, 76)
report["doctors"] = len(docs)
# 3) gallery as-is (small webp)
g = SRC / "netcat_template/template/neoplus_clinic_ru/img/photogallery"
if g.exists():
    (OUT / "gallery").mkdir(parents=True, exist_ok=True)
    for f in sorted(g.glob("*")):
        if f.is_file():
            shutil.copy(f, OUT / "gallery" / f.name)
    report["gallery"] = len(list((OUT / "gallery").glob("*")))
# 4) licenses
for name in ["licimage1.jpg", "licimage2.jpg"]:
    f = SRC / "netcat_template/images" / name
    if f.exists():
        save_webp(f, OUT / "licenses" / (Path(name).stem + ".webp"), 1200, 76)
# 5) review avatars (small)
rsrc = SRC / "netcat_template/template/imgg/img-review"
if rsrc.exists():
    for f in sorted(rsrc.glob("*.jpg")):
        save_webp(f, OUT / "reviews" / (f.stem + ".webp"), 160, 76)
# 6) logo
logo_svg = None
for cand in [SRC / "redisign/assets/img/logoneo.svg"]:
    if cand.exists():
        logo_svg = cand
if logo_svg:
    (OUT / "logo.svg").write_bytes(logo_svg.read_bytes())
    report["logo"] = "svg"
logo_png = SRC / "redisign/assets/img/logoneo.png"
if logo_png.exists():
    shutil.copy(logo_png, OUT / "logo.png")
# 7) misc key photos for home/about (kostrin_/soikin_/kuznetsova/harisova/gromov series + vrach-* webp)
misc_src = SRC / "netcat_template/images"
if misc_src.exists():
    for f in sorted(misc_src.glob("*.jpg")):
        if f.stat().st_size < 250_000:
            shutil.copy(f, OUT / "photos" / f.name)
        else:
            save_webp(f, OUT / "photos" / (f.stem + ".webp"), 900, 70)
for f in sorted((SRC / "netcat_template/neoplus-clinic").glob("*.webp")):
    if f.stat().st_size > 400_000:
        save_webp(f, OUT / "photos" / f.name, 1200, 68)
    else:
        shutil.copy(f, OUT / "photos" / f.name)
# 8) video poster + skip heavy video (note in README)
poster = SRC / "imgs/services/neoplus-videoskrin1.jpg"
if poster.exists():
    save_webp(poster, OUT / "video-poster.webp", 1280, 66)
# og image 1200x630 from a nice clinic photo
og_src = SRC / "imgs/services/vyvod-iz-zapoya-head.webp"
try:
    im = Image.open(og_src).convert("RGB")
    tw, th = 1200, 630
    scale = max(tw / im.width, th / im.height)
    im2 = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left = (im2.width - tw) // 2
    top = (im2.height - th) // 2
    im2.crop((left, top, left + tw, top + th)).save(OUT / "og.webp", "WEBP", quality=70)
    report["og"] = True
except Exception as e:
    print("OG FAIL", e)

count = sum(1 for _ in OUT.rglob("*") if _.is_file())
size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
print("public/img files:", count, f"size: {size/1024/1024:.1f} MB")
print(json.dumps(report, ensure_ascii=False))
