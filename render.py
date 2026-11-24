"""Draw the 24 November 2026 world-news broadsheet (1024x1024 PNG).

Built from a DeepSeek V4.1-Flash draft (via the APInex connector), assembled
and adapted by the Muse session that runs this repo: the layout geometry,
headline fit, pin projection, briefs data and date-check list are this
session's own work, and the model's draft had its vertical flow, map strip
and footer overlaps fixed here. The lead illustration (burning warship in
Benghazi port) is AI-generated and committed as lead art; everything else
is drawn here with Pillow from a fixed, date-checked news brief. No network,
no timestamps in the output: two runs write identical bytes.

Run:  python3 render.py   (writes entry.png next to this file)
"""

import math
import os
from glob import glob

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"

CREAM = "#f7f2e7"
INK = "#141414"
BLACK = "#141414"
WHITE = "#ffffff"
GRAY = (120, 120, 120)
RED = "#b3121b"
NAVY = "#12305a"
YELLOW = "#f2c14e"
W = H = 1024


def load(size, bold=False, serif=False):
    """Load a DejaVu face, falling back to Pillow's built-in bitmap font."""
    if serif and bold:
        names = ["DejaVuSerif-Bold.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
    elif serif:
        names = ["DejaVuSerif.ttf", "DejaVuSans.ttf"]
    elif bold:
        names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
    else:
        names = ["DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def F(sz, b=True):
    return load(sz, bold=b)


def fit(draw, text, max_w, base_size, bold=True, serif=False):
    """Largest size <= base_size at which text fits max_w (deterministic)."""
    size = base_size
    while size > 12:
        font = load(size, bold=bold, serif=serif)
        if draw.textlength(text, font=font) <= max_w:
            return font
        size -= 1
    return load(12, bold=bold, serif=serif)


def wrap(draw, text, font, max_w):
    """Greedy word wrap measured with draw.textlength."""
    lines = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for word in words[1:]:
            trial = cur + " " + word
            if draw.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


img = Image.new("RGB", (W, H), CREAM)
draw = ImageDraw.Draw(img)

f_mast = load(54, bold=True, serif=True)
f_date = load(20)
f_kick = load(16, bold=True)
f_stand = load(16)


def center(text, font, y, fill=INK):
    w = draw.textlength(text, font=font)
    draw.text(((W - w) / 2, y), text, font=font, fill=fill)


# --- masthead -------------------------------------------------------------
center("THE WORLD IN ONE DAY", f_mast, 18)
center("TUESDAY 24 NOVEMBER 2026", f_date, 82)
draw.line([(20, 108), (W - 20, 108)], fill=INK, width=3)
draw.line([(20, 114), (W - 20, 114)], fill=INK, width=1)

# --- lead block -----------------------------------------------------------
LX, LW = 20, 620
draw.text((LX, 130), "LIBYA", font=f_kick, fill=RED)
f_head = fit(draw, "MERKURY SUNK OFF LIBYA", LW, 46)
draw.text((LX, 152), "MERKURY SUNK OFF LIBYA", font=f_head, fill=INK)
f_sub = fit(draw, "UKRAINE'S DRONES SINK A RUSSIAN WARSHIP", LW, 22)
draw.text((LX, 202), "UKRAINE'S DRONES SINK A RUSSIAN WARSHIP", font=f_sub, fill=INK)

standfirst = (
    "Seven Ukrainian sea drones sank the corvette Merkury in Benghazi \u2014 "
    "2,700 km from the front. A Ka-27 helicopter was destroyed and the "
    "cargo ship MV Angara hit."
)
sy = 234
slines = wrap(draw, standfirst, f_stand, LW)
assert len(slines) <= 3, f"standfirst wraps to {len(slines)} lines"
for line in slines:
    draw.text((LX, sy), line, font=f_stand, fill=INK)
    sy += 21

# --- lead illustration ----------------------------------------------------
IX, IY, IW, IH = 20, 300, 620, 100
pasted = False
cands = sorted(glob("lead-merkury*.png"))
if cands:
    try:
        lead = Image.open(cands[0]).convert("RGB")
        # Center-crop to the panel aspect, then resize: deterministic.
        tw, th = lead.size
        target = IW / IH
        if tw / th > target:
            nw = int(th * target)
            x0 = (tw - nw) // 2
            lead = lead.crop((x0, 0, x0 + nw, th))
        else:
            nh = int(tw / target)
            y0 = (th - nh) // 2
            lead = lead.crop((0, y0, tw, y0 + nh))
        lead = lead.resize((IW, IH), Image.LANCZOS)
        img.paste(lead, (IX, IY))
        pasted = True
    except Exception as e:
        print(f"lead art failed: {e}")
        pasted = False

if not pasted:
    draw.rectangle([IX, IY, IX + IW, IY + IH], fill=NAVY)
    draw.ellipse([IX + 34, IY + 14, IX + 86, IY + 66], fill=YELLOW)
    for k in range(3):
        base = IY + 32 + k * 17
        pts = [
            (IX + 140 + x, base + 5 * math.sin(x / 16.0))
            for x in range(0, IW - 180, 5)
        ]
        draw.line(pts, fill="white", width=3)

# --- medium cards ---------------------------------------------------------
def card(x, y, w, h, kick, head, body):
    draw.rectangle([x, y, x + w, y + h], fill=WHITE, outline=BLACK, width=2)
    draw.text((x + 14, y + 11), kick, font=F(13), fill=RED)
    ty = y + 32
    for ln in wrap(draw, head, F(20), w - 28):
        draw.text((x + 14, ty), ln, font=F(20), fill=BLACK)
        ty += 24
    ty += 5
    for ln in wrap(draw, body, F(14, False), w - 28):
        if ty > y + h - 17:
            break
        draw.text((x + 14, ty), ln, font=F(14, False), fill=BLACK)
        ty += 18


card(660, 130, 344, 130, "MARKETS",
     "HUANG IS BACK",
     "Nvidia's board reinstated Jensen Huang as CEO; shares +31%, Nasdaq "
     "+6.5%. US to blacklist chip firm Megaspeed.")

card(660, 270, 344, 130, "GULF",
     "GULF ON EDGE",
     "Iran steps up Gulf attacks and sues for $290bn; US sanctions two "
     "dozen shadow banks; tankers hit mines.")

# --- numbers strip --------------------------------------------------------
draw.rectangle([0, 420, 1024, 500], fill=NAVY)

CELLS = [
    ("+31%", "NVIDIA"),
    ("$290bn", "IRAN CLAIM"),
    ("700,000", "RUSSIAN DEAD"),
    ("24", "BANTEN DEAD"),
    ("53.7", "JAPAN PMI"),
    ("$12bn", "VENEZUELA OIL"),
]
for i, (num, lab) in enumerate(CELLS):
    cx = 1024 * (i + 0.5) / 6
    draw.text((cx, 452), num, font=F(30), fill=WHITE, anchor="mm")
    draw.text((cx, 481), lab, font=F(11), fill=YELLOW, anchor="mm")
    if i:
        draw.line([1024 * i / 6, 432, 1024 * i / 6, 488], fill=CREAM, width=1)

# --- map strip ------------------------------------------------------------
draw.rectangle([0, 520, 1024, 640], fill=WHITE, outline=BLACK, width=2)
draw.text((20, 528), "THE WORLD, PINNED", font=F(14), fill=BLACK)

LAND = [
    (-170, -30, 10, 70),   # Americas
    (-20, 50, -35, 70),    # Europe / Africa
    (50, 180, 0, 75),      # Asia
    (110, 180, -50, 0),    # Oceania
]
for gx in range(40, 985, 14):
    lon = -180 + (gx - 40) * 360.0 / 944.0
    for gy in range(550, 626, 14):
        lat = 80 - (gy - 550) * 140.0 / 75.0
        if any(a <= lon <= b and c <= lat <= d for a, b, c, d in LAND):
            draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=NAVY)


def pin_xy(lon, lat):
    """Map lon/lat onto the dot-grid transform used above."""
    gx = 40 + (lon + 180) * 944.0 / 360.0
    gy = 550 + (80 - lat) * 75.0 / 140.0
    return int(gx), int(gy)


# (number, lon, lat): 1 lead, 2 Huang/Washington, 3 Gulf, 4 Seoul, 5 Kyiv, 6 Banten
PINS = [
    (1, 20.1, 32.1),    # Benghazi
    (2, -77.0, 38.9),   # Washington
    (3, 56.4, 26.7),    # Strait of Hormuz
    (4, 127.0, 37.5),   # Seoul
    (5, 30.5, 50.4),    # Kyiv
    (6, 105.3, -6.0),   # Banten
]
for n, lon, lat in PINS:
    px, py = pin_xy(lon, lat)
    draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=RED, outline=WHITE, width=2)
    draw.text((px, py), str(n), font=F(10), fill=WHITE, anchor="mm")

# --- briefs ---------------------------------------------------------------
# (num, headline, one-liner, date) — verified 23-24 Nov 2026, see research file.
BRIEFS = [
    (4, "Russian jets enter Seoul air zone", "Alert for Ulleung Island.", "24 Nov"),
    (5, "Russia warns Finland, Estonia", "Kyiv warns of new strikes.", "24 Nov"),
    (6, "Kyiv region drone attack kills 11", "Boy pulled alive.", "24 Nov"),
    (7, "Gaza strikes kill three", "Four nations demand aid access.", "24 Nov"),
    (8, "US sanctions Iran shadow banking", "Two dozen entities hit.", "24 Nov"),
    (9, "Iran claims US drone downed", "Tankers hit mines, Guard says.", "24 Nov"),
    (10, "Russia rejects new grain deal", "Tells UN Security Council.", "24 Nov"),
    (11, "Spain's right leads polls", "To oust Sánchez on 29 Nov.", "24 Nov"),
    (12, "Brazil summons Flávio Bolsonaro", "Growth cut to 1.8%.", "24 Nov"),
    (13, "Belgium airports shut", "Anti-austerity strike.", "24 Nov"),
    (14, "FIFA names 2031 hosts", "US, Mexico, Costa Rica, Jamaica.", "24 Nov"),
    (15, "US details $12bn Venezuela oil", "Revenue report published.", "24 Nov"),
    (16, "Modi, Nepal PM open rail link", "Ayodhya–Janakpur express.", "24 Nov"),
    (17, "Lisbon protests cost of living", "Thousands march.", "24 Nov"),
    (18, "Myanmar junta faults ASEAN", "Calls decision unfair.", "24 Nov"),
    (19, "Colombia marks 10 years", "Since FARC peace deal.", "24 Nov"),
    (20, "Measles spreads fast in US", "Doctors warn on old jabs.", "24 Nov"),
    (21, "States sue SpaceX over Grok", "Sexual imagery claims.", "24 Nov"),
    (22, "First Quantum accepts Panama terms", "Cobre talks reopen.", "24 Nov"),
    (23, "Korea rate rise seen Thursday", "To 3.25%, Reuters poll.", "24 Nov"),
    (24, "US weighs training Syrian troops", "Demining, first since 2024.", "23 Nov"),
    (25, "Banten fire toll rises to 24", "Rescue goes on.", "24 Nov"),
    (26, "Trump pauses Iowa blast", "Pending court ruling.", "24 Nov"),
    (27, "Armenia starts Trump Route work", "TRIPP in Syunik.", "24 Nov"),
    (28, "Russia summons Estonian envoy", "Border closure row.", "24 Nov"),
    (29, "EU faults Tajikistan over Putin", "Despite ICC warrant.", "24 Nov"),
    (30, "EU budget questioned", "Central Europe in Bratislava.", "24 Nov"),
    (31, "COP31 aftermath", "Erdogan: failed talks lay basis.", "24 Nov"),
    (32, "ICE detains father, daughter", "At Seattle airport.", "24 Nov"),
    (33, "Verstappen wins Las Vegas GP", "Second straight there.", "23 Nov"),
]

f13b, f13 = load(12, bold=True), load(12)
draw.text((20, 652), "ALSO TODAY", font=load(16, bold=True), fill=BLACK)

overflow = []
for cx, group in ((20, BRIEFS[:15]), (522, BRIEFS[15:30])):
    y = 676
    for i, (num, headline, line, date) in enumerate(group):
        # One row per brief: number + bold headline + line + date.
        draw.text((cx, y), f"{num}.", font=f13b, fill=RED)
        tx = cx + 30
        row = f"{headline} \u2014 {line} ({date})"
        lines = wrap(draw, row, f13, 482 - 30)
        if len(lines) > 1:
            overflow.append((num, row))
        draw.text((tx, y), lines[0], font=f13, fill=BLACK)
        if i < len(group) - 1:
            draw.line([(cx, y + 17), (cx + 482, y + 17)], fill=(200, 200, 200), width=1)
        y += 18
if overflow:
    print("OVERFLOW rows (truncated to first line):", overflow)

# --- date check + footer --------------------------------------------------
draw.rectangle([20, 950, 660, 994], outline=RED, width=2)
f12 = load(12)
dtxt = ("DATE CHECK \u2014 NOT 24 NOV: Shenzhen summit ended 21 Nov; BepiColombo "
        "orbit 21 Nov; Peru quake 22 Nov; Zanzibar fire 21 Nov; Chapo arrest "
        "21 Nov; EU\u2013Indonesia CEPA 22 Nov.")
for k, ln in enumerate(wrap(draw, dtxt, f12, 596)[:2]):
    draw.text((28, 956 + k * 14), ln, font=f12, fill=BLACK)

draw.text((700, 968), "33 STORIES \u00b7 6 REGIONS", font=load(12, bold=True), fill=RED)

f11b = load(11)
draw.text((20, 1002), "Sources: Reuters, AP, BBC, CNN, Al Jazeera, NYT \u2014 "
          "The World in One Day, 24 November 2026.", font=f11b, fill=GRAY)

img.save("entry.png", optimize=True)
print("wrote entry.png")
