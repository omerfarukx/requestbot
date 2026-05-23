"""
RequestBot logo & favicon generator.

Cikti:
  server/frontend/public/  -> favicon.ico, favicon-16.png, favicon-32.png,
                              favicon-96.png, apple-touch-icon.png, og-image.png
  client/                  -> logo.ico  (launcher için)
  (root)                   -> logo.ico  (eski yer, uyumluluk)
"""
import math, os, struct, io
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_SERVER = os.path.join(ROOT, "server", "frontend", "public")
os.makedirs(OUT_SERVER, exist_ok=True)

# ── Renk paleti ─────────────────────────────────────────────────────────────
TOP_COLOR    = (99,  102, 241)   # indigo-500
BOT_COLOR    = (124,  58, 237)   # violet-600
ACCENT       = (167, 139, 250)   # violet-400 (highlight)
TEXT_COLOR   = (255, 255, 255)


def _lerp(a, b, t):
    return int(a + (b - a) * t)


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def create_logo(size: int) -> Image.Image:
    """Diagonal gradient + R on rounded square."""
    # ── gradient ──────────────────────────────────────────────────────────
    grad = Image.new("RGBA", (size, size))
    gd   = ImageDraw.Draw(grad)
    for i in range(size):
        t = i / max(size - 1, 1)
        col = (_lerp(TOP_COLOR[0], BOT_COLOR[0], t),
               _lerp(TOP_COLOR[1], BOT_COLOR[1], t),
               _lerp(TOP_COLOR[2], BOT_COLOR[2], t), 255)
        gd.line([(0, i), (size - 1, i)], fill=col)

    # ── apply rounded mask ────────────────────────────────────────────────
    radius = max(size // 5, 3)
    mask   = _rounded_mask(size, radius)
    grad.putalpha(mask)

    # ── top highlight (shimmer) ───────────────────────────────────────────
    hl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([-size // 3, -size // 2, size + size // 3, size // 2],
               fill=(255, 255, 255, 28))
    hl.putalpha(ImageDraw.Draw(Image.new("L", (size, size))).bitmap if False else hl.split()[3])
    grad = Image.alpha_composite(grad, hl)

    # ── letter "R" ────────────────────────────────────────────────────────
    d = ImageDraw.Draw(grad)

    font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    font_size = max(int(size * 0.56), 6)
    fnt = None
    for fp in font_paths:
        try:
            fnt = ImageFont.truetype(fp, font_size)
            break
        except Exception:
            pass
    if fnt is None:
        fnt = ImageFont.load_default()

    letter = "R"
    bbox = d.textbbox((0, 0), letter, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] - int(size * 0.03)

    # subtle drop-shadow at larger sizes
    if size >= 48:
        d.text((tx + max(size // 40, 1), ty + max(size // 40, 1)),
               letter, font=fnt, fill=(0, 0, 0, 70))

    d.text((tx, ty), letter, font=fnt, fill=TEXT_COLOR + (252,))

    # ── small signal dot (bottom-right) at larger sizes ───────────────────
    if size >= 64:
        dr = max(size // 14, 3)
        dx = int(size * 0.74)
        dy = int(size * 0.72)
        # outer ring
        ring_r = dr + max(size // 22, 2)
        d.ellipse([dx - ring_r, dy - ring_r, dx + ring_r, dy + ring_r],
                  fill=(255, 255, 255, 50))
        # inner dot
        d.ellipse([dx - dr, dy - dr, dx + dr, dy + dr],
                  fill=(255, 255, 255, 230))

    return grad


# ── PNG exports ──────────────────────────────────────────────────────────────

def save_png(img: Image.Image, path: str):
    img.save(path, "PNG")
    print(f"  ✓ {os.path.relpath(path, ROOT)}")


def make_ico(images: list[Image.Image]) -> bytes:
    """Build a proper multi-size .ico file from a list of RGBA images."""
    buf = io.BytesIO()
    num = len(images)
    # ICONDIR header: reserved=0, type=1, count
    buf.write(struct.pack("<HHH", 0, 1, num))
    # We'll write the directory entries after computing offsets
    entries_offset = buf.tell()
    buf.write(b"\x00" * num * 16)   # placeholder for dir entries

    image_data = []
    for img in images:
        w, h = img.size
        png_buf = io.BytesIO()
        img.save(png_buf, format="PNG")
        data = png_buf.getvalue()
        image_data.append((w, h, data))

    # Compute offset of first image
    data_offset = 6 + num * 16
    buf.seek(entries_offset)
    accumulated = data_offset
    for w, h, data in image_data:
        sz = w if w < 256 else 0
        # width, height, colorCount, reserved, planes, bitCount, bytesInRes, imageOffset
        buf.write(struct.pack("<BBBBHHII", sz, sz, 0, 0, 1, 32, len(data), accumulated))
        accumulated += len(data)

    for _, _, data in image_data:
        buf.write(data)

    return buf.getvalue()


# ── Main ─────────────────────────────────────────────────────────────────────

print("\n🎨  RequestBot Logo & Favicon Generator\n")

sizes_server = [16, 32, 96, 180, 512]
imgs = {s: create_logo(s) for s in sizes_server}

# favicon-16/32/96
save_png(imgs[16],  os.path.join(OUT_SERVER, "favicon-16.png"))
save_png(imgs[32],  os.path.join(OUT_SERVER, "favicon-32.png"))
save_png(imgs[96],  os.path.join(OUT_SERVER, "favicon-96.png"))

# apple-touch-icon (180x180)
save_png(imgs[180], os.path.join(OUT_SERVER, "apple-touch-icon.png"))

# favicon.ico (multi-size: 16, 32, 48)
ico_img_48 = create_logo(48)
ico_data = make_ico([imgs[16], imgs[32], ico_img_48])
ico_path = os.path.join(OUT_SERVER, "favicon.ico")
with open(ico_path, "wb") as f:
    f.write(ico_data)
print(f"  ✓ {os.path.relpath(ico_path, ROOT)}")

# og-image.png (1200 x 630)
og = Image.new("RGBA", (1200, 630), (11, 17, 26, 255))
od = ImageDraw.Draw(og)
# Background subtle gradient
for i in range(630):
    t = i / 629
    og.paste(
        Image.new("RGBA", (1200, 1),
                  (_lerp(15, 25, t), _lerp(23, 35, t), _lerp(42, 60, t), 255)),
        (0, i)
    )
# Logo on left
logo_og = create_logo(220)
og.paste(logo_og, (100, (630 - 220) // 2), logo_og)

# Text
og_d = ImageDraw.Draw(og)
fnt_big = fnt_sm = None
for fp in ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]:
    try:
        fnt_big = ImageFont.truetype(fp, 80)
        fnt_sm  = ImageFont.truetype(fp, 34)
        break
    except Exception:
        pass
if fnt_big is None:
    fnt_big = fnt_sm = ImageFont.load_default()

tx_x = 380
og_d.text((tx_x, 180), "RequestBot", font=fnt_big, fill=(255, 255, 255, 255))
og_d.text((tx_x, 285), "Google'da Üst Sıralara Çık", font=fnt_sm, fill=(148, 163, 184, 240))
og_d.text((tx_x, 340), "SEO Trafik Botu  ·  Organik Trafik  ·  Proxy Rotasyonu", font=fnt_sm, fill=(99, 102, 241, 230))

# Accent line under title
line_y = 270
og_d.rectangle([tx_x, line_y, tx_x + 420, line_y + 3], fill=(99, 102, 241, 200))

og_rgb = og.convert("RGB")
og_rgb.save(os.path.join(OUT_SERVER, "og-image.png"), "PNG")
print(f"  ✓ server/frontend/public/og-image.png")

# ── logo.ico for launcher ────────────────────────────────────────────────────
ico_launcher = make_ico([create_logo(s) for s in [16, 32, 48, 64, 128, 256]])
for ico_dest in [
    os.path.join(ROOT, "logo.ico"),
    os.path.join(ROOT, "client", "logo.ico"),
]:
    with open(ico_dest, "wb") as f:
        f.write(ico_launcher)
    print(f"  ✓ {os.path.relpath(ico_dest, ROOT)}")

print("\n✅  Tüm dosyalar oluşturuldu!\n")
