"""
Generate assets/icon.ico using Pillow.
Run once before building:  python installer/make_icon.py
Replace assets/icon.ico with your own 256x256 icon at any time.
"""
import os
from PIL import Image, ImageDraw, ImageFont

SIZES = [256, 128, 64, 48, 32, 16]
OUT   = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")


def make_icon():
    frames = []
    for size in SIZES:
        img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle — dark blue
        margin = size // 12
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=(30, 90, 180, 255),
        )

        # Letter "A" centred
        font_size = int(size * 0.52)
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        text = "A"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1] - size * 0.04),
            text, fill=(255, 255, 255, 255), font=font,
        )
        frames.append(img)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    frames[0].save(OUT, format="ICO", sizes=[(s, s) for s in SIZES], append_images=frames[1:])
    print(f"Icon saved to: {OUT}")


if __name__ == "__main__":
    make_icon()
