"""Generate AcoustiCAD .icns icon — futuristic speaker with sound waves"""
import math
import os
import shutil
from PIL import Image, ImageDraw, ImageFilter


def draw_icon(size):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # ── Background: deep space dark, rounded square ─────────────────────────
    r = s * 0.20
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=r,
                        fill=(10, 12, 22))

    # ── Gradient-style glow behind speaker ─────────────────────────────────
    glow_layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    for i in range(12, 0, -1):
        alpha = int(18 * (1 - i / 13))
        gr = s * (0.08 + i * 0.028)
        gd.ellipse([s/2 - gr, s/2 - gr, s/2 + gr, s/2 + gr],
                   fill=(0, 180, 255, alpha))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(s * 0.04))
    img = Image.alpha_composite(img, glow_layer)
    d = ImageDraw.Draw(img)

    # ── Sound wave arcs (right side) ────────────────────────────────────────
    cx, cy = s * 0.42, s * 0.50
    arc_start, arc_end = -52, 52
    wave_colors = [
        (0, 220, 255, 210),
        (0, 170, 240, 160),
        (0, 120, 210, 110),
    ]
    arc_radii = [s * 0.225, s * 0.310, s * 0.395]
    lw = max(2, int(s * 0.030))
    for i, (wr, wc) in enumerate(zip(arc_radii, wave_colors)):
        # Draw arc as a series of short lines for anti-aliasing
        steps = 80
        pts = []
        for step in range(steps + 1):
            ang = math.radians(arc_start + (arc_end - arc_start) * step / steps)
            pts.append((cx + wr * math.cos(ang), cy + wr * math.sin(ang)))
        for j in range(len(pts) - 1):
            d.line([pts[j], pts[j+1]], fill=wc, width=lw - i)

    # ── Speaker cabinet (rectangle) ─────────────────────────────────────────
    cab_w, cab_h = s * 0.22, s * 0.58
    cab_x = s * 0.20
    cab_y = s * 0.21
    cab_color   = (30, 40, 65)
    cab_border  = (0, 200, 255)
    lw2 = max(2, int(s * 0.025))
    d.rounded_rectangle([cab_x, cab_y, cab_x + cab_w, cab_y + cab_h],
                        radius=s * 0.03, fill=cab_color,
                        outline=cab_border, width=lw2)

    # ── Speaker cone (circle inside cabinet) ────────────────────────────────
    cone_cx = cab_x + cab_w / 2
    cone_cy = cy
    cone_r  = cab_w * 0.38
    # Outer ring
    d.ellipse([cone_cx - cone_r, cone_cy - cone_r,
               cone_cx + cone_r, cone_cy + cone_r],
              outline=(0, 200, 255), width=max(1, int(s * 0.018)))
    # Inner dust cap
    cap_r = cone_r * 0.42
    d.ellipse([cone_cx - cap_r, cone_cy - cap_r,
               cone_cx + cap_r, cone_cy + cap_r],
              fill=(0, 180, 255, 200))

    # ── Tweeter (small circle above cone) ───────────────────────────────────
    tw_r = cab_w * 0.16
    tw_cy = cab_y + s * 0.09
    d.ellipse([cone_cx - tw_r, tw_cy - tw_r,
               cone_cx + tw_r, tw_cy + tw_r],
              outline=(0, 200, 255), width=max(1, int(s * 0.014)))
    d.ellipse([cone_cx - tw_r*0.45, tw_cy - tw_r*0.45,
               cone_cx + tw_r*0.45, tw_cy + tw_r*0.45],
              fill=(0, 200, 255, 200))

    # ── Port (small rect at bottom of cab) ──────────────────────────────────
    port_w, port_h = cab_w * 0.55, s * 0.035
    port_x = cab_x + (cab_w - port_w) / 2
    port_y = cab_y + cab_h - s * 0.075
    d.rounded_rectangle([port_x, port_y, port_x + port_w, port_y + port_h],
                        radius=s*0.008,
                        fill=(0, 160, 230, 180))

    # ── Subtle scanline texture over whole icon ─────────────────────────────
    scan = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    step = max(3, int(s * 0.025))
    for y in range(0, s, step * 2):
        sd.line([(0, y), (s, y)], fill=(0, 0, 0, 18), width=1)
    img = Image.alpha_composite(img, scan)

    return img


def build_icns(out_path):
    iconset_dir = out_path.replace(".icns", ".iconset")
    os.makedirs(iconset_dir, exist_ok=True)

    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for sz in sizes:
        img = draw_icon(sz)
        img.save(os.path.join(iconset_dir, f"icon_{sz}x{sz}.png"))
        if sz <= 512:
            img2 = draw_icon(sz * 2)
            img2.save(os.path.join(iconset_dir, f"icon_{sz}x{sz}@2x.png"))

    os.system(f'iconutil -c icns "{iconset_dir}" -o "{out_path}"')
    shutil.rmtree(iconset_dir)
    print(f"Icon written: {out_path}")


if __name__ == "__main__":
    build_icns("ui/resources/AppIcon.icns")
    draw_icon(512).save("ui/resources/AppIcon_preview.png")
    print("Preview: ui/resources/AppIcon_preview.png")
