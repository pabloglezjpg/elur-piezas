#!/usr/bin/env python3
"""
Comprueba que cada cifra publicada dice lo mismo en TODAS sus superficies.

POR QUÉ EXISTE
Todos los errores graves de este proyecto tienen la misma forma: alguien corrige
un número en el cuerpo y no lo corrige en las otras ocho superficies donde vive.
Pasó con el máximo histórico de Casio, con el «300%» de Argentina —que siguió en
la portada.jpg tres días después de corregirse en el HTML— y con el 93,85 $ de
GoPro. El manifiesto (`<slug>/datos.json`) declara, cifra a cifra, de dónde sale
y en qué superficies aparece; este script comprueba que es verdad.

No sustituye a verificar contra la fuente: comprueba la COHERENCIA INTERNA, que
es lo mecanizable. Que la fuente diga lo que el manifiesto afirma sigue siendo
trabajo de una persona, y por eso cada entrada lleva `url` y `consultado`.

QUÉ HACE FALLAR (salida 1)
  1. Una cifra del manifiesto NO aparece en alguna superficie que ella misma
     declara.
  2. Una entrada sin `url` o sin `consultado`.
  3. Una entrada con `derivado: true` cuyo texto no declara que es cálculo propio.
  4. Una entrada `DINÁMICO` consultada hace más de 60 días.
  5. Una cifra marcada como retirada que sigue viva en alguna superficie.

Uso:
    python3 herramientas/verificar_datos.py            # todas las piezas
    python3 herramientas/verificar_datos.py casio-encogerse
    python3 herramientas/verificar_datos.py --autotest # control positivo
"""

import argparse
import datetime as dt
import glob
import html
import json
import os
import re
import sys

DIAS_DINAMICO = 60


# ── extracción de superficies ────────────────────────────────────────────────

def _meta(doc, attr, valor):
    m = re.search(r'<meta\s+[^>]*%s=["\']%s["\'][^>]*>' % (attr, re.escape(valor)), doc, re.I)
    if not m:
        return ""
    c = re.search(r'content=["\'](.*?)["\']', m.group(0), re.S)
    return html.unescape(c.group(1)) if c else ""


def _bloque(doc, patron):
    m = re.search(patron, doc, re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", m.group(0))) if m else ""


def superficies(doc, portada_doc, slug):
    """Devuelve {nombre_superficie: texto_plano}."""
    s = {}
    t = re.search(r"<title>(.*?)</title>", doc, re.S | re.I)
    s["titulo"] = html.unescape(t.group(1)) if t else ""
    s["meta_description"] = _meta(doc, "name", "description")
    s["og_description"] = _meta(doc, "property", "og:description")
    s["twitter_description"] = _meta(doc, "name", "twitter:description")
    s["og_image_alt"] = _meta(doc, "property", "og:image:alt")
    s["twitter_image_alt"] = _meta(doc, "name", "twitter:image:alt")
    s["jsonld"] = _bloque(doc, r'<script type="application/ld\+json">.*?</script>')
    s["dek"] = _bloque(doc, r'<p class="dek">.*?</p>')
    s["nutgraf"] = _bloque(doc, r'<p class="nutgraf">.*?</p>')
    s["desc_svg"] = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", x))
                             for x in re.findall(r"<desc[^>]*>.*?</desc>", doc, re.S | re.I))
    s["graficos"] = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", x))
                             for x in re.findall(r"<figure[^>]*>.*?</figure>", doc, re.S | re.I))
    s["pie_fuentes"] = _bloque(doc, r'<(?:section|details)[^>]*class="sources[^"]*".*?</(?:section|details)>')
    cuerpo = re.sub(r"<head.*?</head>", " ", doc, flags=re.S)
    cuerpo = re.sub(r"<(script|style|nav|footer|svg).*?</\1>", " ", cuerpo, flags=re.S)
    s["cuerpo"] = html.unescape(re.sub(r"<[^>]+>", " ", cuerpo))
    # La pieza destacada usa <a class="home-feature"> y las demás <a> dentro de
    # <li class="home-card">. Sin las dos, la destacada se quedaba sin comprobar.
    trozos = re.findall(r'<a[^>]*href="%s/"[^>]*>(.*?)</a>' % re.escape(slug), portada_doc, re.S)
    s["tarjeta_portada"] = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", x)) for x in trozos)
    return {k: " ".join(v.split()) for k, v in s.items()}


def aparece(valor, texto):
    """¿Está el valor como NÚMERO COMPLETO, no como trozo de otro más largo?

    La primera versión hacía `valor in texto` y era inútil: al inyectarle un 9
    detrás, «211,4» seguía estando dentro de «211,49» y el control positivo
    pasaba en falso. Un verificador que no puede fallar no verifica nada.
    Ahora el valor no puede ir pegado a otro dígito, coma o punto por ningún
    lado; un «%», un espacio o una letra sí valen como frontera.
    """
    # Frontera: por la izquierda, que no venga pegado a otro dígito, punto o
    # coma. Por la derecha, que no siga un dígito NI un separador decimal con
    # dígito detrás («1.005» dentro de «1.005,5» no vale). Pero una coma o un
    # punto de puntuación normal sí valen como final: «416.161,» es el número.
    borde = r"(?<![\d.,])%s(?![\d])(?![.,]\d)"
    if re.search(borde % re.escape(valor), texto):
        return True
    # segundo intento sin espacios: cubre «1.099 $» escrito con espacio duro
    plano = texto.replace(" ", "").replace("\u00a0", "")
    return bool(re.search(borde % re.escape(valor.replace(" ", "")), plano))


# ── comprobación ─────────────────────────────────────────────────────────────

def revisa(slug, repo, doc=None):
    fallos, avisos, n = [], [], 0
    man_path = os.path.join(repo, slug, "datos.json")
    if not os.path.exists(man_path):
        return None, [], ["sin datos.json"], 0
    man = json.load(open(man_path, encoding="utf-8"))
    doc = doc if doc is not None else open(os.path.join(repo, slug, "index.html"), encoding="utf-8").read()
    portada = open(os.path.join(repo, "index.html"), encoding="utf-8").read()
    sup = superficies(doc, portada, slug)
    hoy = dt.date.today()

    for clave, e in man.get("cifras", {}).items():
        n += 1
        valor = str(e.get("valor", ""))
        if e.get("retirado"):
            # Un hueco declarado suele nombrar la cifra que retira («aquí decía
            # 55%»), y eso NO es que siga viva: es la declaración. Se comprueba
            # sobre el documento sin los bloques de hueco.
            # Se quitan los bloques que DECLARAN un cambio: el hueco declarado,
            # el «Dato retirado» y la nota de «Corrección». Nombrar ahí la cifra
            # vieja es justamente lo que hay que hacer, no un residuo.
            limpio = re.sub(r'<(div|p|section)[^>]*class="[^"]*(hueco|update)[^"]*".*?</\1>',
                            " ", doc, flags=re.S)
            limpio = re.sub(r'<(p|div|li|figcaption)\b[^>]*>((?:(?!</?\1\b).)*?'
                            r'(?:Correcci[óo]n\.|Dato retirado|Hueco declarado)'
                            r'(?:(?!</?\1\b).)*?)</\1>', " ", limpio, flags=re.S)
            sup_limpio = superficies(limpio, portada, slug)
            for nombre, txt in sup_limpio.items():
                if valor and aparece(valor, txt):
                    fallos.append(f"{clave}: marcada RETIRADA y sigue viva en «{nombre}» (fuera del hueco declarado)")
            continue
        if not e.get("url"):
            fallos.append(f"{clave}: sin «url»")
        if not e.get("consultado"):
            fallos.append(f"{clave}: sin «consultado»")
        elif e.get("tipo") == "DINAMICO":
            try:
                d = (hoy - dt.date.fromisoformat(e["consultado"])).days
                if d > DIAS_DINAMICO:
                    fallos.append(f"{clave}: DINÁMICO consultado hace {d} días (máximo {DIAS_DINAMICO})")
            except ValueError:
                fallos.append(f"{clave}: «consultado» no es una fecha ISO")
        if e.get("derivado") and not re.search(r"c[áa]lculo propio", sup["cuerpo"] + sup["pie_fuentes"], re.I):
            fallos.append(f"{clave}: derivado:true y la pieza no dice «cálculo propio» en ninguna parte")
        # Una misma cifra se escribe distinto según la superficie: el titular dice
        # «Tres tazas y media» donde el cuerpo dice «3,5». Se declaran como
        # variantes y vale cualquiera de ellas.
        formas = [valor] + [str(v) for v in e.get("variantes", [])]
        for nombre in e.get("superficies", []):
            if nombre not in sup:
                avisos.append(f"{clave}: superficie desconocida «{nombre}»")
            elif not any(aparece(f, sup[nombre]) for f in formas):
                fallos.append(f"{clave}: «{valor}» NO aparece en «{nombre}»")
    return man, fallos, avisos, n


def autotest(repo):
    """Control positivo: mete un error a propósito y exige que se cace."""
    print("CONTROL POSITIVO — se inyectan errores en memoria, no se toca ningún archivo\n")
    slugs = [d.split("/")[-2] for d in sorted(glob.glob(os.path.join(repo, "*/datos.json")))]
    if not slugs:
        print("  no hay ningún datos.json todavía"); return 1
    fallos_test = 0
    for slug in slugs:
        doc = open(os.path.join(repo, slug, "index.html"), encoding="utf-8").read()
        man, base, _, _ = revisa(slug, repo, doc)
        if base:
            print(f"  ✗ {slug}: la pieza YA falla antes de inyectar nada, el test no vale")
            fallos_test += 1
            continue
        cifras = [(k, v) for k, v in man["cifras"].items()
                  if not v.get("retirado") and v.get("superficies")]
        if not cifras:
            continue
        clave, e = cifras[0]
        valor = str(e["valor"])
        # Se rompen TODAS las apariciones: si solo se rompiera la primera, el
        # test podría estar tocando una superficie que esa cifra no declara y
        # dar un falso «no cazado».
        roto = doc.replace(valor, valor + "9")
        if roto == doc:
            print(f"  ? {slug}: no he podido inyectar el error (valor no literal en el HTML)")
            continue
        _, fallos, _, _ = revisa(slug, repo, roto)
        if fallos:
            print(f"  ✓ {slug}: cazado — {fallos[0]}")
        else:
            print(f"  ✗ {slug}: NO CAZADO. Se rompió «{clave}» ({valor}) y el script dijo que todo bien.")
            fallos_test += 1
    print()
    if fallos_test:
        print(f"CONTROL POSITIVO FALLIDO en {fallos_test} pieza(s). El verificador no sirve.")
        return 1
    print("CONTROL POSITIVO SUPERADO: el verificador caza los errores que se le inyectan.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("piezas", nargs="*")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if a.autotest:
        return autotest(repo)

    slugs = a.piezas or sorted(d.split("/")[-2] for d in glob.glob(os.path.join(repo, "*/index.html"))
                               if os.path.basename(os.path.dirname(d)) != "gracias")
    tot_f = tot_c = con_manifiesto = 0
    sin_manifiesto = []
    for slug in slugs:
        man, fallos, avisos, n = revisa(slug, repo)
        if man is None:
            sin_manifiesto.append(slug)
            continue
        con_manifiesto += 1
        tot_c += n
        tot_f += len(fallos)
        estado = "OK" if not fallos else f"{len(fallos)} FALLO(S)"
        print(f"\n{'='*72}\n{slug}  —  {n} cifras declaradas  —  {estado}")
        for f in fallos:
            print(f"  [FALLO] {f}")
        for w in avisos:
            print(f"  [aviso] {w}")

    print(f"\n{'='*72}")
    print(f"TOTAL: {tot_c} cifras en {con_manifiesto} piezas · {tot_f} fallos")
    if sin_manifiesto:
        print(f"SIN MANIFIESTO ({len(sin_manifiesto)}): {', '.join(sin_manifiesto)}")
    if tot_f:
        print("Hay cifras que no dicen lo mismo en todas sus superficies. No publiques así.")
    return 1 if tot_f else 0


if __name__ == "__main__":
    sys.exit(main())
