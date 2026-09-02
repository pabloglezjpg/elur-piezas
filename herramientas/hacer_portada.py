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
        # Si no cabe arriba, se PEGA al borde superior. Antes bajaba a py+22 y el
        # pie caía justo encima de la línea descendente: en la portada de gopro
        # se leía «ct. 2014» con el «o» tapado, y el primer dígito del dato medio
        # comido. Es la imagen que se ve al compartir el enlace.
        ty = max(y0, ty)
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


def build_stats(cfg, out_path):
    """Maqueta de tres datos en fila, a ancho completo. La usan las piezas cuyo
    resumen son varias cifras y no una curva. Se añadió el 2-sep-2026 porque la
    portada de argentina-milei llevaba «300 → 33%» y esa cifra resultó ser el pico
    de abril de 2024, ya con Milei: el INDEC da 211,4% para los doce meses de 2023.
    La portada no tenía plantilla y por eso se había quedado sin corregir."""
    img = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    d.text((MARGIN, 96), "PIEZAS", font=font(F_MONO_B, 20), fill=INK)
    d.text((MARGIN + d.textlength("PIEZAS", font=font(F_MONO_B, 20)), 96), ".",
           font=font(F_MONO_B, 20), fill=TERRA)

    f_by = font(F_MONO, 15)
    by = "PABLO GONZÁLEZ  ·  PIEZAS.ELUR.ES"
    bw = d.textlength(by, font=f_by)
    d.text((W - MARGIN - bw, 84), by, font=f_by, fill=MUTED)
    d.line([(W - MARGIN - bw, 62), (W - MARGIN, 62)], fill=HAIRLINE, width=1)
    d.line([(W - MARGIN - bw, 122), (W - MARGIN, 122)], fill=HAIRLINE, width=1)

    d.text((MARGIN, 278), cfg["categoria"].upper(), font=font(F_MONO, 17), fill=TERRA)

    f_h1 = font(F_DISPLAY, cfg.get("titular_px", 52))
    y = 326
    for line in wrap(d, cfg["titular"], f_h1, W - 2 * MARGIN):
        d.text((MARGIN, y), line, font=f_h1, fill=INK)
        y += int(f_h1.size * 1.06)

    d.line([(MARGIN, 462), (W - MARGIN, 462)], fill=HAIRLINE, width=1)

    # Ninguna fuente del repo tiene el glifo «→» (U+2192): salía una caja vacía.
    # Se dibuja como vector, que además queda mejor a este tamaño.
    def flecha(x, y_centro, alto):
        largo = int(alto * 0.62)
        d.line([(x, y_centro), (x + largo, y_centro)], fill=TERRA, width=3)
        p = int(alto * 0.17)
        d.polygon([(x + largo + p, y_centro), (x + largo - p, y_centro - p),
                   (x + largo - p, y_centro + p)], fill=TERRA)
        return largo + p

    f_st = font(F_DISPLAY_B, 40)
    f_cap = font(F_MONO, 15)
    x = MARGIN
    for stat in cfg["stats"]:
        desde, hasta, pie = stat if len(stat) == 3 else (stat[0], None, stat[1])
        x_ini = x
        d.text((x, 494), desde, font=f_st, fill=TERRA)
        x += d.textlength(desde, font=f_st)
        if hasta:
            x += 14
            x += flecha(x, 494 + f_st.size // 2 + 2, f_st.size) + 14
            d.text((x, 494), hasta, font=f_st, fill=TERRA)
            x += d.textlength(hasta, font=f_st)
        # El pie se parte en dos líneas si no cabe en su columna. Sin esto, el
        # tercer dato se salía del lienzo: en la portada de cafe-salud el pie
        # acababa cortado por el borde derecho.
        ancho_col = (W - 2 * MARGIN - 2 * 56) // 3
        lineas = wrap(d, pie, f_cap, ancho_col)[:2]
        for j, ln in enumerate(lineas):
            d.text((x_ini, 548 + j * 21), ln, font=f_cap, fill=MUTED)
        ancho_pie = max(d.textlength(ln, font=f_cap) for ln in lineas)
        x = max(x, x_ini + ancho_pie) + 56
        if x > W - MARGIN:
            break

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=92, optimize=True)
    print(f"✓ {out_path}  ({os.path.getsize(out_path)//1024} KB)")


# ── Piezas ───────────────────────────────────────────────────────────────────
PORTADAS = {
    "casio-encogerse": {
        "categoria": "Economía y empresa",
        "titular": "Casio se hizo pequeña para sobrevivir",
        "dek": "Abandonó pantallas, chips, móviles y la cámara digital de consumo que inventó",
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
    # Regenerada dos veces. La 1.ª por datos viejos (−99,2 % y 0,75 $); la 2.ª el
    # 2-sep-2026 porque el 93,85 $ no es el máximo de CIERRE: el 10-K del ejercicio
    # 2015 da 98,47 $ en el 4T de 2014. El −99,4 % aguanta: 1 − 0,60/98,47 = 99,39 %.
    "cafe-salud": {
        "formato": "stats",
        "categoria": "Ciencia · Salud",
        # 2-sep-2026: el titular decía «la ciencia dice que vives un poco más».
        # Kim 2019 publica un riesgo relativo de mortalidad (RR 0,85 a 3,5 tazas),
        # no esperanza de vida: en su abstract no hay ninguna unidad temporal. La
        # portada se rehace anclada a la magnitud que la fuente sí publica.
        "titular": "Tres tazas y media al día: un 15% menos de riesgo de morir",
        "titular_px": 46,
        "stats": [
            ("3,5", "Tazas al día, el punto de menor riesgo"),
            ("−15%", "De mortalidad total frente a quien no toma café"),
            ("Riesgo", "No años de vida: eso no lo mide ningún estudio"),
        ],
    },
    "crisis-memoria-ia": {
        "formato": "stats",
        "categoria": "Tecnología · Consumo",
        # 2-sep-2026: la portada decía «+257%», que era la cifra vieja del SSD y no
        # sale de ninguna pareja publicada por VDURA. El dato real es 3.460 $ →
        # 22.600 $, unas 6,5 veces, que es lo que dicen el cuerpo y los dos alt.
        "titular": "Tu próximo PC, móvil o consola cuesta más por la IA",
        "titular_px": 46,
        "stats": [
            ("×6,5", "Lo que se ha multiplicado un SSD de 30 TB en un año"),
            ("×2,5", "Lo que ha subido un disco duro, que no lleva memoria NAND"),
            ("+93–98%", "La DRAM, en un solo trimestre"),
        ],
    },
    "luz-roja": {
        "formato": "stats",
        "categoria": "Ciencia · Salud",
        "titular": "Luz roja: ciencia vs. marketing",
        # 2-sep-2026: la portada anterior decía «100 → 15%» (supresión de melatonina
        # por color) y «Cero» en quemar grasa. Las dos se han caído en la pieza: los
        # porcentajes no salían de ninguna fuente identificable y se retiró el
        # gráfico entero; y «cero evidencia» es falso, porque la FDA autorizó por
        # De Novo un láser de contorno corporal en 2010 (DEN090008).
        "stats": [
            ("630-700 nm", "La luz roja que usa la fototerapia"),
            ("2", "Usos con evidencia sólida: heridas y mucositis"),
            ("Muy limitada", "Lo que hay en «quemar grasa»"),
        ],
    },
    "argentina-milei": {
        "formato": "stats",
        "categoria": "Economía · Internacional",
        "titular": "Argentina con Milei, sin bandos",
        # 2-sep-2026: era «300 → 33%». El INDEC da 211,4% para los doce meses de
        # 2023 (informe del IPC de diciembre de 2023, «Destacados del mes»). El
        # ~300% era el pico interanual de abril de 2024, ya con Milei.
        "stats": [
            ("211,4", "33%", "Inflación interanual, 2023–2026"),
            ("28,2", "30%", "Pobreza, 2025–1T 2026"),
            ("Superávit", "Resultado fiscal 2024"),
        ],
    },
    "caida-gopro": {
        "categoria": "Economía y empresa",
        "titular": "La caída de GoPro",
        "dek": "Los errores que hicieron desaparecer a la marca de las calles",
        "dato": "−99,4 %",
        "dato_pie": ["de su valor en bolsa", "en una década"],
        "grafico": "linea",
        "serie": [("2014a", 24.0), ("2014", 98.47), ("2018", 6.0),
                  ("2022", 5.5), ("2026", 0.60)],
        "anotaciones": {
            1: ("98,47 $", "4T 2014", -62),
            4: ("0,60 $", "hoy", -62),
        },
    },

    # ── Versiones inglesas ───────────────────────────────────────────────
    # Existen porque las páginas /en/ compartían la portada española: un editor
    # anglófono pegaba el enlace en Slack y la tarjeta salía en español, con
    # puntuación española. El sufijo «-en» escribe portada-en.jpg en la carpeta
    # de la pieza; el diseño es el mismo, cambian las cadenas y el formato
    # numérico (coma de millar, punto decimal).
    "dijeron-que-no-en": {
        "categoria": "Economy & business",
        "titular": "Nobody wanted to buy Netflix",
        "dek": "Blockbuster could have had it for $50 million. And it had its reasons",
        "dato": "6,600\u00d7",
        "dato_pie": ["less than it is worth today", "was what it asked that afternoon"],
        "grafico": "brecha",
        "barra_pequena": ("$50M", 50, "what Netflix asked for in 2000", TERRA),
        "barra_grande": ("$333B", 333000, "what Netflix is worth today", INK),
    },
    "caida-gopro-en": {
        "categoria": "Economy & business",
        "titular": "The fall of GoPro",
        "dek": "The mistakes that made the brand disappear from the streets",
        "dato": "\u2212""99.4 %",
        "dato_pie": ["of its market value", "in a decade"],
        "grafico": "linea",
        "serie": [("2014a", 24.0), ("2014", 98.47), ("2018", 6.0),
                  ("2022", 5.5), ("2026", 0.60)],
        "anotaciones": {
            1: ("$98.47", "Q4 2014", -62),
            4: ("$0.60", "today", -62),
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
        cfg = PORTADAS[slug]
        if slug.endswith("-en"):
            destino = os.path.join(repo, slug[:-3], "portada-en.jpg")
        else:
            destino = os.path.join(repo, slug, "portada.jpg")
        (build_stats if cfg.get("formato") == "stats" else build)(cfg, destino)
