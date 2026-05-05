"""SMMM TAKİP ikon oluşturucu — güzel gradient logo"""
from PIL import Image, ImageDraw, ImageFont
import math, os

OUT = os.path.join(os.path.dirname(__file__), "smmm_icon.ico")

def make_icon():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for sz in sizes:
        img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # ── Arka plan: yuvarlak köşeli dikdörtgen gradient ──
        r = max(sz // 6, 4)
        # Lacivert -> Mor gradient (dikey)
        for y in range(sz):
            t = y / sz
            # Lacivert: (17, 24, 80)  →  Menekşe: (109, 40, 217)
            red   = int(17  + (109 - 17)  * t)
            green = int(24  + (40  - 24)  * t)
            blue  = int(80  + (217 - 80)  * t)
            for x in range(sz):
                # Yuvarlak köşe maskesi
                in_round = (
                    (x >= r and x < sz - r) or
                    (y >= r and y < sz - r) or
                    math.hypot(x - r, y - r) < r or
                    math.hypot(x - (sz-1-r), y - r) < r or
                    math.hypot(x - r, y - (sz-1-r)) < r or
                    math.hypot(x - (sz-1-r), y - (sz-1-r)) < r
                )
                if in_round and (x >= r or x < sz-r) and (y >= r or y < sz-r):
                    img.putpixel((x, y), (red, green, blue, 255))
                elif math.hypot(x - r, y - r) < r or \
                     math.hypot(x - (sz-1-r), y - r) < r or \
                     math.hypot(x - r, y - (sz-1-r)) < r or \
                     math.hypot(x - (sz-1-r), y - (sz-1-r)) < r:
                    img.putpixel((x, y), (red, green, blue, 255))

        # ── Ortaya "₺" sembolü ──
        margin = max(sz // 8, 2)
        text_area = sz - 2 * margin
        font_size = max(int(text_area * 0.60), 8)

        font = None
        font_paths = [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, font_size)
                    break
                except Exception:
                    pass

        symbol = "₺"
        if font:
            bbox = font.getbbox(symbol)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        else:
            tw = th = font_size

        tx = (sz - tw) // 2
        ty = (sz - th) // 2 - bbox[1] if font else (sz - th) // 2

        # Gölge
        if sz >= 32:
            draw.text((tx + 1, ty + 1), symbol, fill=(0, 0, 0, 100), font=font)
        draw.text((tx, ty), symbol, fill=(255, 255, 255, 255), font=font)

        # Üste küçük "S" harfi (sağ üst)
        if sz >= 48:
            small_sz = max(sz // 4, 8)
            try:
                small_font = ImageFont.truetype(font_paths[0], small_sz) if font else None
            except Exception:
                small_font = None
            if small_font:
                draw.text((sz - small_sz - margin//2, margin//2), "S",
                           fill=(255, 220, 100, 240), font=small_font)

        images.append(img)

    images[0].save(OUT, format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    print(f"İkon oluşturuldu: {OUT}")

if __name__ == "__main__":
    make_icon()
