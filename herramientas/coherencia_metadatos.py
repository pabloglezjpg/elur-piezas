#!/usr/bin/env python3
"""
Compara, pieza a pieza, lo que dicen los metadatos con lo que dice el cuerpo.

POR QUÉ EXISTE
La auditoría del 28 de agosto de 2026 encontró un patrón, no casos sueltos: la
capa que más viaja —dek, meta description, Open Graph, Twitter card, JSON-LD y
tarjeta de portada— se escribe aparte del cuerpo verificado y afirma más que él.
El cuerpo acotaba «la cámara digital de consumo con pantalla detrás» y seis
metadatos decían «inventó la cámara digital». El cuerpo explicaba el receptor
OX2R y el dek decía «repone la orexina». La tabla calificaba «Moderada» y el
meta decía «sólida». Ese texto es justo el que lee quien todavía no ha entrado.

QUÉ COMPRUEBA
  1. Toda cifra que aparece en un metadato tiene que aparecer igual en el cuerpo.
     Si no está pero es un redondeo de una cifra del cuerpo -> AVISO.
     Si no está de ninguna forma -> ERROR.
  2. Toda superlativa FACTUAL de un metadato («el mayor», «el primer», «máximo
     histórico», «récord»...) tiene que estar también en el cuerpo. Si no ->
     ERROR. Las absolutas retóricas del titular no cuentan.
  3. Si el cuerpo matiza la frase que lleva esa cifra (se asocia, podría, en
     torno a, según, previsión...) y el metadato no matiza -> AVISO.
  4. La misma cifra no puede diferir entre dos metadatos de la misma pieza.
  5. El titular y el sumario de la tarjeta de portada frente al h1 y al dek.
  6. COBERTURA. Cuenta las superficies que ha sabido leer en cada pieza y la
     compara con la última ejecución, guardada en herramientas/superficies.json.
     Si baja, ERROR. El 31 de agosto de 2026 un cambio de maquetación en la
     portada rompió el patrón de la tarjeta y seis piezas pasaron de 14
     superficies a 12 sin que nada avisara: la herramienta seguía diciendo OK
     mientras dejaba de mirar doce metadatos. Una puerta que se abre sola es
     peor que no tener puerta.

QUÉ NO COMPRUEBA
  No entiende el texto. No detecta una afirmación falsa que use las palabras del
  cuerpo, ni una atribución equivocada. Es una red para el fallo mecánico
  recurrente, no un sustituto de la verificación contra fuente primaria.

USO
    python3 herramientas/coherencia_metadatos.py            # todas las piezas
    python3 herramientas/coherencia_metadatos.py casio-encogerse
    python3 herramientas/coherencia_metadatos.py --solo-errores
Sale con código 1 si hay algún ERROR: sirve como puerta antes de publicar.
"""

import argparse
import glob
import html
import json
import os
import re
import sys
import unicodedata

# Solo superlativas FACTUALES: las que afirman algo comprobable sobre el mundo.
# Se dejan fuera las retóricas del titular («por fin», «nadie», «ninguno»,
# «todas»), que son registro editorial y no una afirmación que verificar; si se
# incluyeran, la herramienta gritaría en cada pieza y se dejaría de mirar.
ABSOLUTOS = [
    "el mayor", "la mayor", "el menor", "la menor",
    "el primer", "el primero", "la primera",
    "el unico", "la unica", "el ultimo", "la ultima",
    "el mejor", "la mejor", "el peor", "la peor",
    "maximo historico", "record", "nunca antes", "por primera vez",
    "el mas alto", "el mas bajo", "la mas alta", "la mas baja",
]
MATICES = [
    "se asocia", "asociado", "asociacion", "podria", "puede", "sugiere",
    "aproximadamente", "en torno a", "unos ", "unas ", "cerca de", "casi",
    "estimacion", "estimado", "prevision", "previsto", "segun", "alrededor de",
    "parece", "apunta", "sobre todo", "de media", "no es causalidad", "matiz",
]


def limpia(t):
    """minúsculas, sin tildes, espacios normalizados"""
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t)


def texto_cuerpo(doc):
    """El texto que el lector encuentra DENTRO de la pieza: prosa, gráficos y
    pies incluidos. Se quitan la cabecera del sitio, el pie, y los elementos
    que son la propia portada del artículo (antetítulo, titular, dek, firma):
    si el dek contara como cuerpo, comparar el dek con el cuerpo sería
    circular y no detectaría nada."""
    s = re.sub(r"<head.*?</head>", " ", doc, flags=re.S)
    s = re.sub(r"<(script|style|nav|footer|header)\b.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<a class=\"skip-link\".*?</a>", " ", s, flags=re.S)
    for cls in ("kicker", "dek", "byline", "headline"):
        s = re.sub(r'<(\w+)[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>.*?</\1>' % cls, " ", s, flags=re.S)
    s = re.sub(r"<h1\b.*?</h1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s))


CIFRA = re.compile(
    # primero la forma con separador de millares (352.258), luego la simple.
    # El guardián final evita que «2010» se lea como «201».
    r"(?<![\w.,])(?:[×x]\s?)?\d{1,3}(?:\.\d{3})+(?:,\d+)?\s?%?(?![\d.,])"
    r"|(?<![\w.,])(?:[×x]\s?)?\d+(?:,\d+)?\s?%?(?![\d.,])"
)


def cifras(t):
    out = []
    for m in CIFRA.finditer(t):
        v = m.group(0).strip()
        if re.fullmatch(r"[×x]?\s?\d{1,2}", v):      # ordinales y años sueltos, demasiado ruido
            continue
        out.append(re.sub(r"\s+", "", v))
    return out


def valor(c):
    n = re.sub(r"[^\d,.]", "", c).replace(".", "").replace(",", ".")
    try:
        return float(n)
    except ValueError:
        return None


def frase_con(t, aguja):
    """La frase del cuerpo que contiene esa cifra. Cadena vacía si no se aísla
    una frase razonable: más vale no avisar que avisar sobre un trozo de nav."""
    partes = re.split(r"(?<=[.;:])\s+(?=[A-ZÁÉÍÓÚÑ¿¡«(])", t)
    patron = re.compile(r"(?<![\d.,])" + re.escape(aguja) + r"(?![\d.,])")
    for f in partes:
        if len(f) <= 400 and patron.search(f):
            return f.strip()
    return ""


def superficies(doc, slug, home):
    s = {}
    def meta(attr, val):
        m = re.search(r'<meta\s+%s="%s"\s+content="([^"]*)"' % (attr, re.escape(val)), doc)
        return html.unescape(m.group(1)) if m else None
    s["title"] = (lambda m: html.unescape(m.group(1)) if m else None)(re.search(r"<title>(.*?)</title>", doc, re.S))
    s["meta description"] = meta("name", "description")
    for k in ("og:title", "og:description", "og:image:alt"):
        s[k] = meta("property", k)
    for k in ("twitter:title", "twitter:description", "twitter:image:alt"):
        s[k] = meta("name", k)
    m = re.search(r'<p class="dek"[^>]*>(.*?)</p>', doc, re.S)
    s["dek"] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip() if m else None
    m = re.search(r"<h1[^>]*>(.*?)</h1>", doc, re.S)
    s["h1"] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip() if m else None
    try:
        ld = json.loads(re.findall(r"application/ld\+json[^>]*>(.*?)</script>", doc, re.S)[0])
        s["JSON-LD headline"] = ld.get("headline")
        s["JSON-LD description"] = ld.get("description")
    except Exception:
        s["JSON-LD"] = None
    # el rótulo de la tarjeta puede llevar dentro la cifra clave (<b class="home-card-fig">),
    # así que no se puede exigir que no haya etiquetas dentro del span
    pat = re.compile(r'<a href="%s/">\s*<span class="home-card-tag">.*?</span>\s*'
                     r'<span class="home-card-title">([^<]*)</span>\s*'
                     r'<span class="home-card-desc">([^<]*)</span>' % re.escape(slug), re.S)
    m = pat.search(home)
    if not m:
        m = re.search(r'class="home-feature[^"]*" href="%s/".*?<h2>(.*?)</h2>\s*'
                      r'<p class="home-dek">(.*?)</p>' % re.escape(slug), home, re.S)
    if m:
        s["tarjeta titular"] = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        s["tarjeta sumario"] = html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
    return {k: v for k, v in s.items() if v}


COBERTURA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "superficies.json")


def lee_cobertura():
    try:
        with open(COBERTURA, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"AVISO: no se ha podido leer {COBERTURA} ({e}). Se tratará como primera ejecución.")
        return None


def escribe_cobertura(datos):
    with open(COBERTURA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def revisa_cobertura(actual, previo):
    """Devuelve la lista de piezas que han perdido superficies comprobadas."""
    if previo is None:
        return []
    caidas = []
    for slug, antes in sorted(previo.items()):
        ahora = actual.get(slug)
        if ahora is None:
            caidas.append((slug, antes, 0, "la pieza ya no se comprueba"))
        elif ahora < antes:
            caidas.append((slug, antes, ahora, "hay metadatos que han dejado de mirarse"))
    return caidas


def revisa(slug, home, solo_errores=False):
    ruta = os.path.join(slug, "index.html")
    doc = open(ruta, encoding="utf-8").read()
    cuerpo = texto_cuerpo(doc)
    cuerpo_l = limpia(cuerpo)
    sup = superficies(doc, slug, home)
    cuerpo_cifras = set(cifras(cuerpo))
    cuerpo_vals = [v for v in (valor(c) for c in cuerpo_cifras) if v is not None]

    fallos = []
    vistas = {}
    for nombre, texto in sup.items():
        if nombre in ("h1", "dek"):
            es_meta = False          # el dek y el h1 son la pieza, sirven de referencia
        else:
            es_meta = True
        tl = limpia(texto)

        for c in cifras(texto):
            if c in cuerpo_cifras:
                v = valor(c)
                if v is not None:
                    vistas.setdefault(round(v, 4), []).append((nombre, c))
                # ¿el cuerpo matiza donde el metadato no?
                if es_meta:
                    fc = limpia(frase_con(cuerpo, c.replace("%", "")))
                    if fc and any(m in fc for m in MATICES) and not any(m in tl for m in MATICES):
                        fallos.append(("AVISO", nombre,
                                       f"«{c}»: el cuerpo la matiza y el metadato la da en firme",
                                       frase_con(cuerpo, c.replace("%", ""))[:160]))
                continue
            v = valor(c)
            cercana = None
            if v:
                for w in cuerpo_vals:
                    if w and abs(w - v) / max(abs(w), 1) < 0.02 and w != v:
                        cercana = w
                        break
            if cercana:
                fallos.append(("AVISO", nombre,
                               f"«{c}» no está en el cuerpo; parece redondeo de {cercana:g}", ""))
            else:
                fallos.append(("ERROR", nombre,
                               f"«{c}» no aparece en el cuerpo de la pieza", ""))
            if v is not None:
                vistas.setdefault(round(v, 4), []).append((nombre, c))

        if es_meta:
            for a in ABSOLUTOS:
                if re.search(r"\b" + re.escape(a), tl) and not re.search(r"\b" + re.escape(a), cuerpo_l):
                    fallos.append(("ERROR", nombre,
                                   f"superlativa factual «{a}» que el cuerpo no sostiene", texto[:160]))

    # misma magnitud escrita de dos formas distintas entre superficies
    for v, apar in vistas.items():
        formas = {c for _, c in apar}
        if len(formas) > 1:
            fallos.append(("AVISO", "coherencia entre superficies",
                           "la misma cifra se escribe de formas distintas: " +
                           "; ".join(f"{n} «{c}»" for n, c in apar), ""))

    # tarjeta de portada frente a la pieza
    if "tarjeta titular" in sup and "h1" in sup and sup["tarjeta titular"] != sup["h1"]:
        fallos.append(("AVISO", "tarjeta de portada",
                       "el titular de la tarjeta no es el h1 de la pieza",
                       f"tarjeta: {sup['tarjeta titular']} || h1: {sup['h1']}"))
    if "tarjeta sumario" in sup and "dek" in sup and sup["tarjeta sumario"] != sup["dek"]:
        fallos.append(("AVISO", "tarjeta de portada",
                       "el sumario de la tarjeta no es el dek de la pieza", ""))

    if solo_errores:
        fallos = [f for f in fallos if f[0] == "ERROR"]
    return sup, fallos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("piezas", nargs="*")
    ap.add_argument("--solo-errores", action="store_true")
    args = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(repo)
    home = open("index.html", encoding="utf-8").read()

    slugs = args.piezas or [d.split("/")[0] for d in sorted(glob.glob("*/index.html"))]
    slugs = [s for s in slugs if s != "gracias"]

    errores = avisos = 0
    cobertura = {}
    for slug in slugs:
        sup, fallos = revisa(slug, home, args.solo_errores)
        e = sum(1 for f in fallos if f[0] == "ERROR")
        a = len(fallos) - e
        errores += e
        avisos += a
        cobertura[slug] = len(sup)
        estado = "OK" if not fallos else f"{e} ERROR · {a} AVISO"
        print(f"\n{'='*72}\n{slug}  —  {len(sup)} superficies  —  {estado}")
        for nivel, donde, que, ctx in fallos:
            print(f"  [{nivel}] {donde}: {que}")
            if ctx:
                print(f"          {ctx}")

    print(f"\n{'='*72}\nTOTAL: {errores} ERROR · {avisos} AVISO en {len(slugs)} piezas")
    if errores:
        print("Hay metadatos que afirman algo que el cuerpo no dice. No publiques así.")

    # ── control de cobertura ──
    previo = lee_cobertura()
    # solo se compara contra las piezas que se han pedido en esta ejecución
    previo_filtrado = {k: v for k, v in previo.items() if k in cobertura} if previo else None
    caidas = revisa_cobertura(cobertura, previo_filtrado)
    if caidas:
        print(f"\n{'='*72}")
        print("ERROR DE COBERTURA. La herramienta comprueba menos que en la ejecución anterior:")
        for slug, antes, ahora, motivo in caidas:
            print(f"  [ERROR] {slug}: {antes} superficies -> {ahora}. {motivo}.")
        print("\nCasi siempre significa que ha cambiado la maquetación y un patrón de")
        print("lectura ha dejado de encajar, no que sobre un metadato. Arregla el patrón")
        print("antes de publicar. Si la bajada es intencionada (una pieza que de verdad")
        print("pierde una superficie), borra su entrada de:")
        print(f"  {COBERTURA}")
        print("y vuelve a ejecutar, dejando constancia de por qué.")
        errores += len(caidas)
    else:
        base = dict(previo or {})
        base.update(cobertura)   # el techo solo sube
        if base != (previo or {}):
            escribe_cobertura(base)
        if previo is None:
            print(f"\nCobertura registrada por primera vez en {COBERTURA} ({len(cobertura)} piezas).")

    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
