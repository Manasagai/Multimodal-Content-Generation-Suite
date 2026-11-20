# multimodal_suite/local_engine.py
"""Offline engine: campaign copy, image analysis and image rendering with no external AI API."""
import io
import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageStat

ASPECT_SIZES = {"1:1": (1024, 1024), "4:5": (1024, 1280), "9:16": (720, 1280), "16:9": (1280, 720)}

COLOR_WORDS = {
    "purple": (139, 92, 246), "violet": (139, 92, 246), "pink": (236, 72, 153),
    "magenta": (217, 70, 239), "red": (239, 68, 68), "orange": (249, 115, 22),
    "yellow": (250, 204, 21), "gold": (212, 175, 55), "green": (34, 197, 94),
    "blue": (59, 130, 246), "teal": (20, 184, 166), "cyan": (34, 211, 238),
    "white": (245, 245, 245), "black": (20, 20, 24), "brown": (120, 72, 40),
    "beige": (222, 205, 170), "navy": (30, 41, 90), "grey": (140, 140, 150),
    "gray": (140, 140, 150), "silver": (190, 190, 200),
}


def use_gemini() -> bool:
    return os.getenv("USE_GEMINI", "false").strip().lower() == "true"


def _words(text):
    return re.findall(r"[a-z]+", (text or "").lower())


def _nearest_colour_name(rgb):
    best, best_d = "neutral", 1e9
    for name, ref in COLOR_WORDS.items():
        d = sum((rgb[i] - ref[i]) ** 2 for i in range(3))
        if d < best_d:
            best, best_d = name, d
    return best


def _tone_phrase(tone):
    t = (tone or "").lower()
    if "eco" in t:
        return "natural and responsible"
    if "professional" in t:
        return "clear and credible"
    if "friendly" in t:
        return "warm and approachable"
    if "playful" in t:
        return "fun and energetic"
    if "luxury" in t or "premium" in t:
        return "refined and premium"
    return "confident and clear"


def local_campaign_brief(product_name, product_description, target_audience,
                         marketing_objective, platforms, brand_tone):
    name = (product_name or "Your product").strip()
    desc = (product_description or "").strip()
    first = re.split(r"(?<=[.!?])\s+", desc)[0] if desc else ""
    tone = _tone_phrase(brand_tone)
    plats = [p for p in (platforms or []) if p] or ["social media"]
    audience = (target_audience or "your audience").strip().rstrip(".")
    objective = (marketing_objective or "grow awareness").strip().rstrip(".")
    tag = re.sub(r"[^A-Za-z0-9]", "", name) or "Product"
    plat_tag = re.sub(r"[^A-Za-z0-9]", "", plats[0].title()) or "Social"
    return {
        "headline": f"{name}: made for everyday moments",
        "tagline": f"{name}. {tone[0].upper() + tone[1:]} care you can count on.",
        "product_description": desc or f"{name} is designed for {audience}.",
        "captions": [
            f"Meet {name}. {first or 'Designed to fit into your routine.'} Tap the link to learn more.",
            f"For {audience}: {name} keeps things simple. Our goal is to {objective}.",
            f"Ready to try {name}? Share it with someone who would love it.",
        ],
        "hashtags": ["#" + tag, "#NewLaunch", "#" + plat_tag],
        "ctas": [f"Discover {name}", "See how it works", "Get yours today"],
        "visual_concept": f"Clean product shot of {name} in soft natural light, matching a {tone} brand tone, with simple supporting props.",
    }


def local_image_analysis(image_path):
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    small = img.resize((160, max(1, int(160 * h / w))))
    gray = small.convert("L")
    g_stat = ImageStat.Stat(gray)
    brightness, contrast = g_stat.mean[0], g_stat.stddev[0]
    sat = ImageStat.Stat(small.convert("HSV")).mean[1]
    sw, sh = small.size
    centre = gray.crop((int(sw * 0.25), int(sh * 0.25), int(sw * 0.75), int(sh * 0.75)))
    c_std = ImageStat.Stat(centre).stddev[0]
    centred = c_std >= contrast * 0.9
    names = []
    q = small.quantize(colors=4).convert("RGB")
    colours = q.getcolors(maxcolors=100000) or []
    for count, rgb in sorted(colours, reverse=True):
        n = _nearest_colour_name(rgb)
        if n not in names:
            names.append(n)
    if not names:
        names = ["neutral"]
    orient = "portrait" if h > w else ("landscape" if w > h else "square")
    composition = (f"{orient.capitalize()} frame at {w}x{h}px. " + (
        "The main subject sits near the centre, so it is easy to read at a glance."
        if centred else
        "Visual weight is spread toward the edges, so the product may compete with the background."))
    colour = (f"Dominant colours: {', '.join(names[:3])}. " + (
        "The colours are vivid, which stands out in a busy feed."
        if sat > 110 else
        "The colours are muted, which feels calm but may be less eye-catching."))
    visibility = (f"Average brightness {brightness:.0f}/255 with contrast {contrast:.0f}. " + (
        "Strong contrast makes the product easy to see."
        if contrast > 55 else
        "Low contrast means the product may blend into the background."))
    score = max(1, min(10, round((contrast / 64) * 5 + (sat / 255) * 5)))
    effectiveness = (f"Estimated visual impact: {score}/10, based on contrast and colour saturation. "
                     "This is a rule-based check, not a judgement by an AI model.")
    brand = ("Keep the same two or three colours across every post. This image is built mainly on "
             + names[0] + (f" and {names[1]}." if len(names) > 1 else "."))
    tips = []
    if contrast <= 55:
        tips.append("Increase contrast between the product and the background.")
    if sat <= 110:
        tips.append("Add one bold accent colour to draw the eye.")
    if not centred:
        tips.append("Move the product closer to the centre.")
    tips.append("Leave clear space near the top for headline text.")
    return {
        "composition": composition,
        "color_combination": colour,
        "product_visibility": visibility,
        "marketing_effectiveness": effectiveness,
        "brand_consistency": brand,
        "improvement_suggestions": " ".join(tips),
    }


def _font(size):
    for path in ["C:\\Windows\\Fonts\\arialbd.ttf", "C:\\Windows\\Fonts\\arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _text_w(font, text):
    try:
        return font.getlength(text)
    except AttributeError:
        return font.getsize(text)[0]


def _fit_font(text, max_w, start):
    size = start
    while size > 12:
        f = _font(size)
        if _text_w(f, text) <= max_w:
            return f
        size -= 4
    return _font(12)


def _label_text(prompt):
    quoted = re.findall(r'"([^"]{2,40})"', prompt or "")
    if quoted:
        return quoted[0][:24]
    words = (prompt or "").split()[:2]
    return (" ".join(words).title()[:24]) or "PRODUCT"


def local_render_image(prompt, aspect="1:1"):
    w, h = ASPECT_SIZES.get(aspect, (1024, 1024))
    found = [COLOR_WORDS[x] for x in _words(prompt) if x in COLOR_WORDS]
    base = found[0] if found else (139, 92, 246)
    accent = found[1] if len(found) > 1 else (236, 72, 153)
    img = Image.new("RGBA", (w, h))
    bg = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(base[i] * (1 - t) + accent[i] * t) for i in range(3)) + (255,)
        bg.line([(0, y), (w, y)], fill=col)
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = w // 2, int(h * 0.55)
    max_r = int(min(w, h) * 0.40)
    for r in range(max_r, 0, -max(1, max_r // 25)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 10))
    bw, bh = int(w * 0.30), int(h * 0.56)
    x0, y0 = cx - bw // 2, int(h * 0.20)
    cap_h = int(bh * 0.14)
    d.ellipse((cx - int(bw * 0.6), y0 + bh - 20, cx + int(bw * 0.6), y0 + bh + 30), fill=(0, 0, 0, 90))
    d.rounded_rectangle((x0 + int(bw * 0.12), y0, x0 + int(bw * 0.88), y0 + cap_h),
                        radius=int(bw * 0.06), fill=(30, 30, 36, 255))
    d.rounded_rectangle((x0, y0 + cap_h - 4, x0 + bw, y0 + bh),
                        radius=int(bw * 0.14), fill=(250, 250, 252, 255))
    lb0, lb1 = y0 + int(bh * 0.38), y0 + int(bh * 0.80)
    d.rectangle((x0, lb0, x0 + bw, lb1), fill=tuple(accent) + (255,))
    d.rounded_rectangle((x0 + int(bw * 0.10), y0 + cap_h + 10, x0 + int(bw * 0.20), y0 + bh - 20),
                        radius=6, fill=(255, 255, 255, 140))
    label = _label_text(prompt)
    font = _fit_font(label, bw * 0.84, int(w * 0.06))
    tw = _text_w(font, label)
    d.text((cx - tw / 2, lb0 + (lb1 - lb0) * 0.30), label, font=font, fill=(255, 255, 255, 255))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
