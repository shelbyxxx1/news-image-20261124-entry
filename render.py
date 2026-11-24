"""Typeset the 24 November 2026 front page and write entry.png (1024x1024).

The page is a dense broadsheet: masthead, one illustrated lead, two side
stories, a numbers band, a dotted world map with pins, thirty dated briefs
and a date-check box. Everything is drawn with Pillow from the fixed brief
below; the lead photograph is an AI-generated picture committed next to this
file. No network access, no clock reads, so repeated runs are byte-identical.

Local build only:  python3 render.py
"""

import math
import os
from glob import glob

from PIL import Image, ImageDraw, ImageFont

DEJAVU = "/usr/share/fonts/truetype/dejavu/"
PAGE = 1024
PAPER = "#f7f2e7"
INK = "#141414"
SNOW = "#ffffff"
MUTED = (120, 120, 120)
SCARLET = "#b3121b"
DEEP = "#12305a"
GOLD = "#f2c14e"
MARGIN = 20
LEAD_WIDTH = 620
HAIRLINE = (200, 200, 200)


def get_font(points, bold=False, serif=False):
    """Pick a DejaVu face; fall back to Pillow's bitmap font if missing."""
    if serif:
        chain = ["DejaVuSerif-Bold.ttf", "DejaVuSans-Bold.ttf"] if bold else [
            "DejaVuSerif.ttf", "DejaVuSans.ttf"]
    elif bold:
        chain = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]
    else:
        chain = ["DejaVuSans.ttf"]
    for face in chain:
        try:
            return ImageFont.truetype(os.path.join(DEJAVU, face), points)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def headline_font(draw, text, width, top_size, bold=True, serif=False):
    """Shrink a one-line headline until it fits, never below 12 points."""
    size = top_size
    while size > 12:
        face = get_font(size, bold=bold, serif=serif)
        if draw.textlength(text, font=face) <= width:
            return face
        size -= 1
    return get_font(12, bold=bold, serif=serif)


def wrap_lines(draw, text, face, width):
    """Greedy wrap measured with the real font metrics."""
    out = []
    for chunk in text.split("\n"):
        words = chunk.split()
        if not words:
            out.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = current + " " + word
            if draw.textlength(trial, font=face) <= width:
                current = trial
            else:
                out.append(current)
                current = word
        out.append(current)
    return out


def centered(draw, text, face, y, fill=INK):
    """Draw one line centred on the page."""
    span = draw.textlength(text, font=face)
    draw.text(((PAGE - span) / 2, y), text, font=face, fill=fill)


def draw_masthead(draw):
    centered(draw, "THE WORLD IN ONE DAY",
             get_font(54, bold=True, serif=True), 18)
    centered(draw, "TUESDAY 24 NOVEMBER 2026", get_font(20), 82)
    draw.line([(MARGIN, 108), (PAGE - MARGIN, 108)], fill=INK, width=3)
    draw.line([(MARGIN, 114), (PAGE - MARGIN, 114)], fill=INK, width=1)


def draw_lead(canvas, draw):
    """Lead story: kicker, fitted headline, sub-head, standfirst, picture."""
    draw.text((MARGIN, 130), "LIBYA",
              font=get_font(16, bold=True), fill=SCARLET)
    head = headline_font(draw, "MERKURY SUNK OFF LIBYA", LEAD_WIDTH, 46)
    draw.text((MARGIN, 152), "MERKURY SUNK OFF LIBYA", font=head, fill=INK)
    sub = headline_font(draw, "UKRAINE'S DRONES SINK A RUSSIAN WARSHIP",
                        LEAD_WIDTH, 22)
    draw.text((MARGIN, 202), "UKRAINE'S DRONES SINK A RUSSIAN WARSHIP",
              font=sub, fill=INK)

    standfirst = (
        "Seven Ukrainian sea drones sank the corvette Merkury in Benghazi "
        "\u2014 2,700 km from the front. A Ka-27 helicopter was destroyed "
        "and the cargo ship MV Angara hit."
    )
    face = get_font(16)
    rows = wrap_lines(draw, standfirst, face, LEAD_WIDTH)
    assert len(rows) <= 3, f"standfirst wraps to {len(rows)} lines"
    y = 234
    for row in rows:
        draw.text((MARGIN, y), row, font=face, fill=INK)
        y += 21

    # Picture panel: centre-crop the committed lead art to the panel shape.
    px, py, pw, ph = MARGIN, 300, LEAD_WIDTH, 100
    shown = False
    for path in sorted(glob("lead-merkury*.png")):
        try:
            art = Image.open(path).convert("RGB")
            aw, ah = art.size
            want = pw / ph
            if aw / ah > want:
                cut = int(ah * want)
                off = (aw - cut) // 2
                art = art.crop((off, 0, off + cut, ah))
            else:
                cut = int(aw / want)
                off = (ah - cut) // 2
                art = art.crop((0, off, aw, off + cut))
            canvas.paste(art.resize((pw, ph), Image.LANCZOS), (px, py))
            shown = True
            break
        except Exception as err:
            print(f"lead art failed ({path}): {err}")
    if not shown:
        draw.rectangle([px, py, px + pw, py + ph], fill=DEEP)
        draw.ellipse([px + 34, py + 14, px + 86, py + 66], fill=GOLD)
        for k in range(3):
            base = py + 32 + k * 17
            wave = [(px + 140 + x, base + 5 * math.sin(x / 16.0))
                    for x in range(0, pw - 180, 5)]
            draw.line(wave, fill="white", width=3)


def story_card(draw, x, y, w, h, kicker, head, body):
    """One white side-story box with a red kicker and wrapped body."""
    draw.rectangle([x, y, x + w, y + h], fill=SNOW, outline=INK, width=2)
    draw.text((x + 14, y + 11), kicker,
              font=get_font(13, bold=True), fill=SCARLET)
    ty = y + 32
    for row in wrap_lines(draw, head, get_font(20, bold=True), w - 28):
        draw.text((x + 14, ty), row, font=get_font(20, bold=True), fill=INK)
        ty += 24
    ty += 5
    for row in wrap_lines(draw, body, get_font(14), w - 28):
        if ty > y + h - 17:
            break
        draw.text((x + 14, ty), row, font=get_font(14), fill=INK)
        ty += 18


def draw_side_stories(draw):
    story_card(draw, 660, 130, 344, 130, "MARKETS", "HUANG IS BACK",
               "Nvidia's board reinstated Jensen Huang as CEO; shares +31%, "
               "Nasdaq +6.5%. US to blacklist chip firm Megaspeed.")
    story_card(draw, 660, 270, 344, 130, "GULF", "GULF ON EDGE",
               "Iran steps up Gulf attacks and sues for $290bn; US sanctions "
               "two dozen shadow banks; tankers hit mines.")


def draw_numbers(draw):
    """Navy band with six big figures from the day."""
    draw.rectangle([0, 420, PAGE, 500], fill=DEEP)
    figures = [
        ("+31%", "NVIDIA"),
        ("$290bn", "IRAN CLAIM"),
        ("700,000", "RUSSIAN DEAD"),
        ("24", "BANTEN DEAD"),
        ("53.7", "JAPAN PMI"),
        ("$12bn", "VENEZUELA OIL"),
    ]
    for i, (big, small) in enumerate(figures):
        cx = PAGE * (i + 0.5) / 6
        draw.text((cx, 452), big, font=get_font(30, bold=True),
                  fill=SNOW, anchor="mm")
        draw.text((cx, 481), small, font=get_font(11, bold=True),
                  fill=GOLD, anchor="mm")
        if i:
            draw.line([PAGE * i / 6, 432, PAGE * i / 6, 488],
                      fill=PAPER, width=1)


def draw_world_map(draw):
    """Dotted continents with six numbered pins for the biggest stories."""
    draw.rectangle([0, 520, PAGE, 640], fill=SNOW, outline=INK, width=2)
    draw.text((MARGIN, 528), "THE WORLD, PINNED",
              font=get_font(14, bold=True), fill=INK)

    continents = [
        {"lon": (-170, -30), "lat": (10, 70)},    # the Americas
        {"lon": (-20, 50), "lat": (-35, 70)},     # Europe and Africa
        {"lon": (50, 180), "lat": (0, 75)},       # Asia
        {"lon": (110, 180), "lat": (-50, 0)},     # Oceania
    ]

    def project(lon, lat):
        gx = 40 + (lon + 180) * 944.0 / 360.0
        gy = 550 + (80 - lat) * 75.0 / 140.0
        return int(gx), int(gy)

    for gx in range(40, 985, 14):
        lon = -180 + (gx - 40) * 360.0 / 944.0
        for gy in range(550, 626, 14):
            lat = 80 - (gy - 550) * 140.0 / 75.0
            if any(box["lon"][0] <= lon <= box["lon"][1] and
                   box["lat"][0] <= lat <= box["lat"][1]
                   for box in continents):
                draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=DEEP)

    # number, longitude, latitude: 1 lead, 2 Huang, 3 Gulf, 4 Seoul, 5 Kyiv, 6 Banten
    pins = [
        (1, 20.1, 32.1),
        (2, -77.0, 38.9),
        (3, 56.4, 26.7),
        (4, 127.0, 37.5),
        (5, 30.5, 50.4),
        (6, 105.3, -6.0),
    ]
    for num, lon, lat in pins:
        px, py = project(lon, lat)
        draw.ellipse([px - 9, py - 9, px + 9, py + 9],
                     fill=SCARLET, outline=SNOW, width=2)
        draw.text((px, py), str(num), font=get_font(10, bold=True),
                  fill=SNOW, anchor="mm")


# (number, headline, one-liner, date) — verified 23-24 Nov 2026, see research file.
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


def draw_briefs(draw):
    """Thirty briefs in two columns of fifteen, one row each."""
    draw.text((MARGIN, 652), "ALSO TODAY",
              font=get_font(16, bold=True), fill=INK)
    num_face = get_font(12, bold=True)
    text_face = get_font(12)
    too_long = []
    for col_x, group in ((MARGIN, BRIEFS[:15]), (522, BRIEFS[15:30])):
        y = 676
        for i, (num, head, line, date) in enumerate(group):
            draw.text((col_x, y), f"{num}.", font=num_face, fill=SCARLET)
            row = f"{head} \u2014 {line} ({date})"
            rows = wrap_lines(draw, row, text_face, 482 - 30)
            if len(rows) > 1:
                too_long.append((num, row))
            draw.text((col_x + 30, y), rows[0], font=text_face, fill=INK)
            if i < len(group) - 1:
                draw.line([(col_x, y + 17), (col_x + 482, y + 17)],
                          fill=HAIRLINE, width=1)
            y += 18
    if too_long:
        print("OVERFLOW rows (truncated to first line):", too_long)


def draw_footer(draw):
    """Date-check box, story count and the source line."""
    draw.rectangle([MARGIN, 950, 660, 994], outline=SCARLET, width=2)
    face = get_font(12)
    note = ("DATE CHECK \u2014 NOT 24 NOV: Shenzhen summit ended 21 Nov; "
            "BepiColombo orbit 21 Nov; Peru quake 22 Nov; Zanzibar fire "
            "21 Nov; Chapo arrest 21 Nov; EU\u2013Indonesia CEPA 22 Nov.")
    for k, row in enumerate(wrap_lines(draw, note, face, 596)[:2]):
        draw.text((28, 956 + k * 14), row, font=face, fill=INK)
    draw.text((700, 968), "33 STORIES \u00b7 6 REGIONS",
              font=get_font(12, bold=True), fill=SCARLET)
    draw.text((MARGIN, 1002),
              "Sources: Reuters, AP, BBC, CNN, Al Jazeera, NYT \u2014 "
              "The World in One Day, 24 November 2026.",
              font=get_font(11), fill=MUTED)


def main():
    canvas = Image.new("RGB", (PAGE, PAGE), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw_masthead(draw)
    draw_lead(canvas, draw)
    draw_side_stories(draw)
    draw_numbers(draw)
    draw_world_map(draw)
    draw_briefs(draw)
    draw_footer(draw)
    canvas.save("entry.png", optimize=True)
    print("wrote entry.png")


if __name__ == "__main__":
    main()
