#!/usr/bin/env python3
"""
Generador de portadas (og:image) para piezas.elur.es — 1200x630.

Usa las fuentes reales del repo (Fraunces, Newsreader, IBM Plex Mono) y los
colores del sistema, así que la portada sale igual que la web.

Uso:
    python3 herramientas/hacer_portada.py <slug>

Los slugs configurados están abajo, en PORTADAS. Para añadir una pieza nueva,
copia un bloque y cambia los textos. No hace falta saber diseño.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ── Sistema visual ───────────────────────────────────────────────────────────
W, H = 1200, 630
PAPER = "#F4EFE4"
INK = "#191510"
TERRA = "#B84A2C"
MUTED = "#8A8178"
TERRA_SOFT = (184, 74, 44, 38)      # relleno de área bajo la curva
HAIRLINE = "#D6CDBC"

FONTS = "/tmp/fonts"                 # ver README de esta carpeta
F_DISPLAY = f"{FONTS}/fraunces-900.ttf"
F_DISPLAY_B = f"{FONTS}/fraunces-700.ttf"
F_BODY = f"{FONTS}/newsreader-400.ttf"
F_MONO = f"{FONTS}/plexmono-400.ttf"
F_MONO_B = f"{FONTS}/plexmono-600.ttf"

MARGIN = 64


def font(path, size):
    return ImageFont.truetype(path, size)


def tracked(draw, xy, text, fnt, fill, tracking=0.0):
    """Dibuja texto con letter-spacing. Devuelve el ancho total."""
    x, y = xy
    extra = fnt.size * tracking
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + extra
    return x - xy[0]


def tracked_width(draw, text, fnt, tracking=0.0):
    extra = fnt.size * tracking
    return sum(draw.textlength(c, font=fnt) + extra for c in text)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        test = f"{cur} {wd}".strip()
        if draw.textlength(test, font=fnt) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# ── Gráficos de apoyo ────────────────────────────────────────────────────────
def chart_line(img, draw, box, serie, etiquetas):
    """Curva simple con área. serie: [(label, valor)]. etiquetas: índices a anotar."""
    x0, y0, x1, y1 = box
    vals = [v for _, v in serie]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    pad_top, pad_bot = 58, 46
    n = len(serie)
    pts = []
    for i, (_, v) in enumerate(serie):
        px = x0 + (x1 - x0) * i / (n - 1)
        py = y1 - pad_bot - (y1 - y0 - pad_top - pad_bot) * (v - lo) / span
        pts.append((px, py))

    area = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(area).polygon(pts + [(pts[-1][0], y1 - pad_bot), (pts[0][0], y1 - pad_bot)],
                                 fill=TERRA_SOFT)
    img.alpha_composite(area)

    draw.line([(x0, y1 - pad_bot), (x1, y1 - pad_bot)], fill=HAIRLINE, width=2)
    draw.line(pts, fill=TERRA, width=5, joint="curve")

    f_val = font(F_MONO_B, 21)
    f_cap = font(F_MONO, 16)
    for idx, (txt, cap, dy) in etiquetas.items():
        px, py = pts[idx]
        col = TERRA if idx == len(serie) - 1 else INK
        draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=col)
        tw = max(draw.textlength(txt, font=f_val), draw.textlength(cap, font=f_cap))
        tx = min(px + 20, x1 - tw)          # nunca se sale por la derecha
        ty = py + dy
        if ty < y0:                          # si choca arriba, la etiqueta baja
            ty = py + 22
        draw.text((tx, ty), txt, font=f_val, fill=INK)
        draw.text((tx, ty + 26), cap, font=f_cap, fill=MUTED)


def chart_gap(img, draw, box, small, big):
    """Dos barras a escala real. Sirve para enseñar una diferencia brutal."""
    x0, y0, x1, y1 = box
    bar_h, gap = 62, 118
    top = y0 + 76
    f_lab = font(F_MONO_B, 19)
    f_cap = font(F_MONO, 16)
    max_w = x1 - x0

    for i, (label, val, cap, color) in enumerate([small, big]):
        y = top + i * (bar_h + gap)
        w = max(4, max_w * val / big[1])
        draw.rectangle([x0, y, x0 + w, y + bar_h], fill=color)
        draw.text((x0, y - 30), label, font=f_lab, fill=INK)
        draw.text((x0 + (w + 14 if w < 220 else 14), y + bar_h + 12), cap,
                  font=f_cap, fill=MUTED)


# ── Montaje ──────────────────────────────────────────────────────────────────
def build(cfg, out_path):
    img = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Antetítulo + firma del sitio
    tracked(d, (MARGIN, 58), cfg["categoria"].upper(), font(F_MONO_B, 19), TERRA, 0.19)
    f_wm = font(F_MONO_B, 19)
    wm = "PIEZAS"
    wm_w = tracked_width(d, wm, f_wm, 0.19)
    x_wm = W - MARGIN - wm_w - d.textlength(".", font=f_wm)
    tracked(d, (x_wm, 58), wm, f_wm, INK, 0.19)
    d.text((x_wm + wm_w, 58), ".", font=f_wm, fill=TERRA)

    col_w = cfg.get("col_w", 560)

    # Titular
    f_h1 = font(F_DISPLAY, cfg.get("titular_px", 74))
    y = 112
    for line in wrap(d, cfg["titular"], f_h1, col_w):
        d.text((MARGIN, y), line, font=f_h1, fill=INK)
        y += int(f_h1.size * 1.06)

    # Dek
    y += 30
    f_dek = font(F_BODY, 27)
    for line in wrap(d, cfg["dek"], f_dek, col_w):
        d.text((MARGIN, y), line, font=f_dek, fill=INK)
        y += int(f_dek.size * 1.34)

    # Dato grande
    f_stat = font(F_DISPLAY_B, cfg.get("dato_px", 86))
    stat_y = H - 158
    d.text((MARGIN, stat_y), cfg["dato"], font=f_stat, fill=TERRA)
    sw = d.textlength(cfg["dato"], font=f_stat)
    f_sc = font(F_MONO, 17)
    for i, line in enumerate(cfg["dato_pie"]):
        d.text((MARGIN + sw + 18, stat_y + 38 + i * 25), line, font=f_sc, fill=INK)

    # Pie
    d.text((MARGIN, H - 52), "piezas.elur.es  ·  Pablo González",
           font=font(F_MONO, 16), fill=MUTED)

    # Visual
    box = (660, 132, W - MARGIN, H - 96)
    if cfg.get("grafico") == "linea":
        chart_line(img, d, box, cfg["serie"], cfg["anotaciones"])
    elif cfg.get("grafico") == "brecha":
        chart_gap(img, d, box, cfg["barra_pequena"], cfg["barra_grande"])

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=92, optimize=True)
    print(f"✓ {out_path}  ({os.path.getsize(out_path)//1024} KB)")


# ── Piezas ───────────────────────────────────────────────────────────────────
PORTADAS = {
    "casio-encogerse": {
        "categoria": "Economía y empresa",
        "titular": "Casio se hizo pequeña para sobrevivir",
        "dek": "Abandonó pantallas, chips, móviles y las cámaras que ella misma inventó",
        "dato": "+62,1 %",
        "dato_pie": ["de beneficio operativo", "en un solo ejercicio"],
        "grafico": "linea",
        # Beneficio operativo consolidado, miles de millones de yenes.
        # Fuente: Casio, Medium-Term Management Plan, 14-may-2026, p. 3.
        "serie": [("2022", 22.0), ("2023", 18.2), ("2024", 14.2),
                  ("2025", 14.2), ("2026", 23.1)],
        "anotaciones": {
            2: ("14,2", "el suelo, 2024", -62),
            4: ("23,1", "marzo 2026", -62),
        },
    },
    "dijeron-que-no": {
        "categoria": "Economía y empresa",
        "titular": "Nadie quería comprar Netflix",
        "dek": "Blockbuster pudo quedársela por 50 millones. Y tenía sus motivos",
        "dato": "6.600×",
        "dato_pie": ["menos de lo que vale hoy", "lo que pedía aquella tarde"],
        "grafico": "brecha",
        "barra_pequena": ("50 M$", 50, "lo que pedía Netflix en 2000", TERRA),
        "barra_grande": ("333.000 M$", 333000, "lo que vale Netflix hoy", INK),
    },
    # Regenerada: la anterior llevaba los datos viejos (−99,2 % y 0,75 $).
    "caida-gopro": {
        "categoria": "Economía y empresa",
        "titular": "La caída de GoPro",
        "dek": "Los errores que hicieron desaparecer a la marca de las calles",
        "dato": "−99,4 %",
        "dato_pie": ["de su valor en bolsa", "en una década"],
        "grafico": "linea",
        "serie": [("2014a", 24.0), ("2014", 93.85), ("2018", 6.0),
                  ("2022", 5.5), ("2026", 0.60)],
        "anotaciones": {
            1: ("93,85 $", "oct. 2014", -62),
            4: ("0,60 $", "hoy", -62),
        },
    },
}


if __name__ == "__main__":
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pedidos = sys.argv[1:] or list(PORTADAS)
    for slug in pedidos:
        if slug not in PORTADAS:
            print(f"✗ no conozco «{slug}». Disponibles: {', '.join(PORTADAS)}")
            continue
        build(PORTADAS[slug], os.path.join(repo, slug, "portada.jpg"))
