#!/usr/bin/env python3
"""
Recalcula el tiempo de lectura de las piezas y lo deja igual en los dos sitios
donde vive: la propia pieza y su tarjeta en la portada.

NORMA DE LA CASA: 225 palabras por minuto sobre TODO el texto visible de la
página (se descuentan cabecera, navegación, pie, scripts, estilos y el interior
de los SVG). 225 ppm es el ritmo habitual de lectura atenta en español para
texto analítico; usar una cifra única y reproducible evita lo que había antes,
que iba de 81 a 194 ppm según la pieza.

Uso:
    python3 herramientas/tiempo_lectura.py            # informe, no toca nada
    python3 herramientas/tiempo_lectura.py --aplicar  # escribe los cambios
    python3 herramientas/tiempo_lectura.py --aplicar --salvo casio-encogerse
"""

import argparse
import glob
import html
import os
import re

PPM = 225


def palabras(doc: str) -> int:
    s = re.sub(r"<head.*?</head>", "", doc, flags=re.S)
    s = re.sub(r"<(script|style|nav|footer|svg).*?</\1>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return len(html.unescape(s).split())


def minutos(n: int) -> int:
    return max(1, round(n / PPM))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--salvo", nargs="*", default=[],
                    help="slugs que no hay que tocar (p. ej. si otro proceso los está editando)")
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo)

    home = open("index.html", encoding="utf-8").read()
    home_original = home
    print(f"{'pieza':<24}{'palabras':>9}{'antes':>8}{'ahora':>8}")

    for ruta in sorted(glob.glob("*/index.html")):
        slug = ruta.split("/")[0]
        doc = open(ruta, encoding="utf-8").read()
        m = re.search(r"(Lectura[^<]*?)(\d+)(\s*min)", doc)
        if not m:
            continue
        n = palabras(doc)
        if n < 300:
            continue
        nuevo = minutos(n)
        marca = "  (saltada)" if slug in args.salvo else ""
        print(f"{slug:<24}{n:>9}{m.group(2):>6} min{nuevo:>6} min{marca}")

        if slug in args.salvo:
            continue

        if args.aplicar and m.group(2) != str(nuevo):
            doc = doc[:m.start()] + m.group(1) + str(nuevo) + m.group(3) + doc[m.end():]
            open(ruta, "w", encoding="utf-8").write(doc)

        # la tarjeta de la portada tiene que decir lo mismo
        home = re.sub(
            rf'(<a href="{re.escape(slug)}/">.*?home-card-meta">[^·]*·\s*)\d+(\s*min)',
            rf"\g<1>{nuevo}\g<2>", home, flags=re.S)
        home = re.sub(
            rf'(class="home-feature[^"]*" href="{re.escape(slug)}/".*?home-feature-meta">[^·]*·\s*)\d+(\s*min)',
            rf"\g<1>{nuevo}\g<2>", home, flags=re.S)

    if args.aplicar and home != home_original:
        open("index.html", "w", encoding="utf-8").write(home)
        print("\nPortada actualizada.")
    elif not args.aplicar:
        print("\n(informe solamente — usa --aplicar para escribir)")


if __name__ == "__main__":
    main()
