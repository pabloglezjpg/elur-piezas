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

# El nombre del sitio. Decisión del 3 de septiembre de 2026: PIEZAS también en la
# edición inglesa, porque es el dominio y es la marca — un medio no traduce su
# cabecera. Vivía como literal en tres maquetas distintas y por eso se quedó
# partido en dos idiomas durante un día. Ahora se escribe una vez.
MARCA = "PIEZAS"


def font(path, size):
    return ImageFont.truetype(path, size)


def marca(d, cfg, y, px, tracking, derecha=True):
    """Dibuja «PIEZAS.» con el punto en rojo, y devuelve dónde termina.

    Una pieza puede sobreescribirlo con «marca» en su configuración, pero piénsalo
    dos veces: la cabecera es la misma en todo el sitio, y tenerla en un solo sitio
    es justo lo que impide que vuelva a quedarse partida entre idiomas."""
    txt = (cfg or {}).get("marca", MARCA)
    f = font(F_MONO_B, px)
    ancho = tracked_width(d, txt, f, tracking)
    punto = d.textlength(".", font=f)
    x = (W - MARGIN - ancho - punto) if derecha else MARGIN
    x += tracked(d, (x, y), txt, f, INK, tracking)
    d.text((x, y), ".", font=f, fill=TERRA)
    return x + punto


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
    marca(d, cfg, 58, 19, 0.19)

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

    marca(d, cfg, 96, 20, 0.0, derecha=False)

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


def _cabecera(d, cfg, y_kicker=62):
    """Antetítulo a la izquierda y la marca a la derecha. Común a las maquetas."""
    tracked(d, (MARGIN, y_kicker), cfg["categoria"].upper(), font(F_MONO_B, 17), TERRA, 0.14)
    marca(d, cfg, y_kicker, 20, 0.14)


def _pie(d, y=568):
    d.text((MARGIN, y), "piezas.elur.es  \u00b7  Pablo Gonz\u00e1lez",
           font=font(F_MONO, 15), fill=MUTED)


def build_ancla(cfg, out_path):
    """Titular a la izquierda, curva a la derecha y dos anclas abajo unidas por un
    conector. Es la maqueta de tim-cook-apple y apple-upgrade, que hasta ahora
    vivían como JPG sueltos: nadie podía regenerarlos, que es exactamente como la
    portada de argentina-milei se quedó tres días diciendo «300%»."""
    img = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    _cabecera(d, cfg)

    # ── Titular y dek, columna izquierda
    ancho = cfg.get("ancho_texto", 660)
    f_h1 = font(F_DISPLAY, cfg.get("titular_px", 52))
    y = cfg.get("titular_y", 128)
    for line in wrap(d, cfg["titular"], f_h1, ancho):
        d.text((MARGIN, y), line, font=f_h1, fill=INK)
        y += int(f_h1.size * 1.08)
    if cfg.get("dek"):
        f_dek = font(F_BODY, 26)
        y += 12
        for line in wrap(d, cfg["dek"], f_dek, ancho):
            d.text((MARGIN, y), line, font=f_dek, fill=INK)
            y += int(f_dek.size * 1.32)

    # ── Curva de apoyo, columna derecha. Es un apunte, no un gráfico con ejes:
    #    no lleva escala y por eso no rotula ningún valor.
    gx0, gx1 = cfg.get("curva_x", (730, 1135))
    gy0, gy1 = cfg.get("curva_y", (205, 380))
    d.line([(gx0, gy0), (gx1, gy0)], fill=HAIRLINE, width=1)
    d.line([(gx0, gy1 + 55), (gx1, gy1 + 55)], fill=HAIRLINE, width=1)
    guia = cfg.get("guia", INK)
    paso = 14
    for x in range(gx0, gx1, paso):
        d.line([(x, gy0 + 34), (min(x + 8, gx1), gy0 + 34)], fill=guia, width=3)
    d.line([(gx0, gy1 + 48), (gx1, gy0 + 60)], fill=TERRA, width=4)
    if cfg.get("punto", True):
        d.ellipse([gx1 - 8, gy0 + 52, gx1 + 8, gy0 + 68], fill=TERRA)

    # ── Anclas: etiqueta pequeña, cifra grande y pie opcional
    f_lab = font(F_MONO, 15)
    f_big = font(F_DISPLAY_B, 44)
    f_con = font(F_MONO, 17)
    x = MARGIN
    y_lab, y_big = cfg.get("ancla_y", 470), cfg.get("ancla_y", 470) + 24
    anclas = cfg["anclas"]
    for i, a in enumerate(anclas):
        etiqueta, cifra, pie, color = a
        tracked(d, (x, y_lab), etiqueta.upper(), f_lab, MUTED, 0.08)
        d.text((x, y_big), cifra, font=f_big, fill=color)
        ancho_a = max(tracked_width(d, etiqueta.upper(), f_lab, 0.08),
                      d.textlength(cifra, font=f_big))
        if pie:
            d.text((x, y_big + 58), pie, font=f_lab, fill=MUTED)
            ancho_a = max(ancho_a, d.textlength(pie, font=f_lab))
        x += ancho_a + 34
        if i == 0 and cfg.get("conector"):
            cw = d.textlength(cfg["conector"], font=f_con)
            d.text((x, y_big + 16), cfg["conector"], font=f_con, fill=MUTED)
            x += cw + 34

    # Si alguna ancla lleva pie, el crédito baja: en la primera tirada
    # «piezas.elur.es · Pablo González» se montó encima de «never yours».
    hay_pie = any(a[2] for a in anclas)
    _pie(d, cfg.get("pie_y", 596 if hay_pie else 568))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=92, optimize=True)
    print(f"\u2713 {out_path}  ({os.path.getsize(out_path)//1024} KB)")


def build_cifra(cfg, out_path):
    """Una cifra enorme a la izquierda con su pie, y el titular a la derecha.
    Maqueta de cultura-financiera."""
    img = Image.new("RGBA", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    _cabecera(d, cfg, 66)

    f_n = font(F_DISPLAY, cfg.get("cifra_px", 168))
    d.text((MARGIN, 130), cfg["cifra"], font=f_n, fill=TERRA)
    x = MARGIN + d.textlength(cfg["cifra"], font=f_n)
    if cfg.get("sufijo"):
        f_s = font(F_DISPLAY, cfg.get("sufijo_px", 74))
        d.text((x, 130 + f_n.size - f_s.size - 26), cfg["sufijo"], font=f_s, fill=TERRA)

    f_pie = font(F_MONO, 16)
    y = cfg.get("pie_cifra_y", 340)
    for line in wrap(d, cfg["pie_cifra"], f_pie, 300):
        d.text((MARGIN, y), line, font=f_pie, fill=INK)
        y += 26

    f_h1 = font(F_DISPLAY, cfg.get("titular_px", 44))
    yh = cfg.get("titular_y", 262)
    for line in wrap(d, cfg["titular"], f_h1, W - 440 - MARGIN):
        d.text((440, yh), line, font=f_h1, fill=INK)
        yh += int(f_h1.size * 1.16)

    d.line([(MARGIN, 520), (W - MARGIN, 520)], fill=INK, width=2)
    tracked(d, (MARGIN, 548), "PABLO GONZ\u00c1LEZ", font(F_MONO_B, 16), INK, 0.1)
    f_u = font(F_MONO, 16)
    url = cfg["url"]
    d.text((W - MARGIN - d.textlength(url, font=f_u), 548), url, font=f_u, fill=MUTED)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=92, optimize=True)
    print(f"\u2713 {out_path}  ({os.path.getsize(out_path)//1024} KB)")


def build_panel(cfg, out_path):
    """Titular a la izquierda y un panel gráfico a la derecha. El panel NO se
    redibuja: se toma de la portada española de la misma pieza, para que las dos
    versiones enseñen exactamente la misma imagen y no dos simulaciones distintas.
    Solo se reescribe su rótulo. Maqueta de musk-ceguera."""
    base = Image.open(cfg["panel_de"]).convert("RGBA")
    corte = cfg.get("panel_x", 620)
    img = Image.new("RGBA", (W, H), PAPER)
    img.paste(base.crop((corte, 0, W, H)), (corte, 0))
    d = ImageDraw.Draw(img)

    # El rótulo del panel va sobre negro: se tapa y se reescribe.
    if cfg.get("rotulo"):
        # La caja tapa SOLO la banda del rótulo. Con 28 px de alto recortaba la
        # primera fila de puntos del panel.
        rx0, ry0, rx1, ry1 = cfg.get("rotulo_caja", (760, 24, W - 24, 46))
        # El negro del panel no se adivina: se muestrea del propio JPEG. Con un
        # hex a ojo el parche se veía como un recuadro más claro sobre el fondo.
        muestra = [base.getpixel((x, ry0 - 10))[:3]
                   for x in range(int(rx0), int(rx1), 7)]
        fondo = max(set(muestra), key=muestra.count)
        d.rectangle([rx0, ry0, rx1, ry1], fill=fondo)
        f_r = font(F_MONO, 15)
        w_r = tracked_width(d, cfg["rotulo"], f_r, 0.1)
        tracked(d, (rx1 - w_r, ry0 + 6), cfg["rotulo"], f_r, "#CFC6B8", 0.1)

    ancho = corte - MARGIN - 40
    tracked(d, (MARGIN, 56), cfg["categoria"].upper(), font(F_MONO_B, 17), TERRA, 0.14)

    f_h1 = font(F_DISPLAY, cfg.get("titular_px", 46))
    y = cfg.get("titular_y", 96)
    for line in wrap(d, cfg["titular"], f_h1, ancho):
        d.text((MARGIN, y), line, font=f_h1, fill=INK)
        y += int(f_h1.size * 1.12)
    if cfg.get("dek"):
        f_dek = font(F_BODY, 23)
        y += 14
        for line in wrap(d, cfg["dek"], f_dek, ancho):
            d.text((MARGIN, y), line, font=f_dek, fill=INK)
            y += int(f_dek.size * 1.34)

    f_big = font(F_DISPLAY, 52)
    f_lab = font(F_MONO, 15)
    x = MARGIN
    for cifra, pie in cfg["stats"]:
        d.text((x, 440), cifra, font=f_big, fill=TERRA)
        lineas = wrap(d, pie, f_lab, 245)[:2]
        for j, ln in enumerate(lineas):
            d.text((x, 508 + j * 21), ln, font=f_lab, fill=INK)
        x += max(d.textlength(cifra, font=f_big),
                 max(d.textlength(ln, font=f_lab) for ln in lineas)) + 40
    _pie(d, 562)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=92, optimize=True)
    print(f"\u2713 {out_path}  ({os.path.getsize(out_path)//1024} KB)")


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
    "casio-encogerse-en": {
        "categoria": "Economy & business",
        "titular": "Casio made itself smaller to survive",
        "dek": "It dropped displays, chips, phones and the consumer digital camera it invented",
        "dato": "+62.1 %",
        "dato_pie": ["of operating profit", "in a single financial year"],
        "grafico": "linea",
        "serie": [("2022", 22.0), ("2023", 18.2), ("2024", 14.2),
                  ("2025", 14.2), ("2026", 23.1)],
        "anotaciones": {
            2: ("14.2", "the floor, 2024", -62),
            4: ("23.1", "March 2026", -62),
        },
    },
    "cafe-salud-en": {
        "formato": "stats",
        "categoria": "Science & health",
        "titular": "Three and a half cups a day: 15% lower risk of dying",
        "titular_px": 46,
        "stats": [
            ("3.5", "Cups a day, the point of lowest risk"),
            ("\u221215%", "In all-cause mortality vs drinking no coffee"),
            ("Risk", "Not years of life: no study measures that"),
        ],
    },
    "crisis-memoria-ia-en": {
        "formato": "stats",
        "categoria": "Technology \u00b7 Consumer",
        "titular": "Your next PC, phone or console costs more because of AI",
        "titular_px": 46,
        "stats": [
            ("6.5\u00d7", "What a 30 TB SSD has multiplied by in a year"),
            ("2.5\u00d7", "What a hard drive went up, and it carries no NAND memory"),
            ("+93\u201398%", "DRAM, in a single quarter"),
        ],
    },
    "luz-roja-en": {
        "formato": "stats",
        "categoria": "Science & health",
        "titular": "Red light: science vs marketing",
        "stats": [
            ("630-700 nm", "The red light that phototherapy uses"),
            ("2", "Uses with solid evidence: wounds and mucositis"),
            ("Very limited", "What there is on \u201cfat burning\u201d"),
        ],
    },
    "argentina-milei-en": {
        "formato": "stats",
        "categoria": "Economy \u00b7 International",
        "titular": "Argentina under Milei, without picking a side",
        "stats": [
            ("211.4", "33%", "Year-on-year inflation, 2023\u20132026"),
            ("28.2", "30%", "Poverty, 2025\u2013Q1 2026"),
            ("Surplus", "2024 fiscal balance"),
        ],
    },
    # La portada española dice «CIENCIA · NEUROLOGÍA» y el antetítulo de la pieza
    # dice «Ciencia · Salud». La inglesa se alinea con SU página, no con el JPG
    # español. La discrepancia del par español queda reportada, no tocada.
    "narcolepsia-orexina-en": {
        "formato": "stats",
        "categoria": "Science \u00b7 Health",
        "titular": "Narcolepsy: the cause, not just the symptom",
        "stats": [
            ("FDA", "Approves Orzeyful (oveporexton) on 5 August 2026"),
            ("2 \u00b7 273", "Phase 3 trials, double-blind, placebo-controlled"),
            ("~20 years", "Since orexin was identified as a target"),
        ],
    },
    # Mismo aviso: el JPG español dice «EMPRESA Y TECNOLOGÍA», el antetítulo de la
    # pieza dice «Economía · Empresa». La inglesa sigue a la página.
    "tim-cook-apple-en": {
        "formato": "ancla",
        "categoria": "Economy \u00b7 Business",
        "titular": "Tim Cook: the man who made Apple 13 times bigger",
        "titular_px": 50,
        "anclas": [
            ("August 2011", "$350,000M", None, TERRA),
            ("7 Aug 2026", "$4.57 trillion", None, TERRA),
        ],
        "conector": "13\u00d7",
        "guia": INK,
    },
    "apple-upgrade-en": {
        "formato": "ancla",
        "categoria": "Economy \u00b7 Business",
        "titular": "Apple wants you to rent your next iPhone",
        "titular_px": 50,
        "dek": "Apple Upgrade turns the hardware into one more subscription",
        "anclas": [
            ("Rent, 24 months", "$767.76", "never yours", TERRA),
            ("Buy it", "$1,099", "yours from day 1", INK),
        ],
        "conector": "vs",
        "guia": "#3F5A63",
    },
    "cultura-financiera-en": {
        "formato": "cifra",
        "categoria": "Economy \u00b7 Spain",
        "cifra": "19",
        "sufijo": "%",
        "pie_cifra": "of Spanish adults get all three basic money questions right \u2014 the three the OECD asks worldwide",
        "titular": "Do we really have no financial literacy?",
        "url": "piezas.elur.es/cultura-financiera/en",
    },
    "musk-ceguera-en": {
        "formato": "panel",
        "categoria": "Neurotechnology",
        "titular": "Musk promises to restore sight. In Elche they already have.",
        "titular_px": 44,
        "dek": "What is real today in brain implants for sight \u2014 and what is only a promise.",
        "stats": [
            ("0", "patients with Blindsight (Neuralink)"),
            ("2", "people already see shapes, in Elche"),
        ],
        "panel_de": "musk-ceguera/portada.jpg",
        "rotulo": "SIMULATION \u00b7 CORTICAL IMPLANT",
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
        MAQUETAS = {"stats": build_stats, "ancla": build_ancla,
                    "cifra": build_cifra, "panel": build_panel}
        MAQUETAS.get(cfg.get("formato"), build)(cfg, destino)
