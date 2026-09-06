#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verifica_pieza.py — la puerta. Verde o rojo, y en rojo dice qué falla.

    python3 verifica_pieza.py <slug> [<slug>...]      una o varias piezas
    python3 verifica_pieza.py --todas                 las doce
    python3 verifica_pieza.py --repo ~/Desktop/elur-piezas <slug>
    python3 verifica_pieza.py --solo-control          solo prueba la báscula
    python3 verifica_pieza.py --sin-render <slug>     sin navegador (sale con 2)
    python3 verifica_pieza.py --json <slug>           salida para otra máquina

CÓDIGOS DE SALIDA — y no son intercambiables

    0   VERDE. El control positivo saltó y la pieza pasa.
    1   ROJO. La pieza falla. Debajo está qué y dónde.
    2   LA BÁSCULA ESTÁ ROTA. Falta una herramienta, o el control positivo NO
        saltó. No es lo mismo que esté rota la pieza a que esté rota la báscula,
        y por eso son códigos distintos. Un 2 NUNCA se lee como verde.

EL CONTROL POSITIVO VA DELANTE, EN CADA EJECUCIÓN

Antes de mirar la pieza de verdad, este guion rompe una copia a propósito —una
rotura por cada familia de comprobación— y exige que cada rotura suene. Si una
no suena, se para ahí y sale con 2 sin llegar a evaluar nada.

Existe por un caso real de este proyecto: `piezas.elur.es` devolvió durante días
200 con la portada para cualquier ruta inexistente. Cada comprobación de «esta
URL da 200» fue basura y nadie lo supo, porque todo daba verde. Un verde solo
significa algo si en esa misma ejecución se ha demostrado que el rojo era
posible.

QUÉ MIRA, Y POR QUÉ ESTAS COSAS

Las nueve familias son, una a una, un error que ya ha mordido en este repo. No
son buenas prácticas genéricas.

POR QUÉ NO BASTA scrollWidth === clientWidth
`assets/periodismo.css:49` declara `html,body{overflow-x:hidden}`, así que la
medida global da verde por construcción en TODAS las páginas de este sitio. Lo
avisa el propio manual (CLAUDE.md:202-205) y aquí está el CSS que lo hace. La
medida que mide es la de por elemento, en `lib/sonda_overflow.js`.

QUÉ NO HACE
Compara la pieza consigo misma y con sus superficies. No sale a comprobar que
una fuente diga lo que la pieza afirma: eso sigue siendo trabajo de una persona,
y por eso cada entrada del manifiesto lleva `url` y `consultado`.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "lib"))
import arbol  # noqa: E402

SONDA = os.path.join(AQUI, "lib", "sonda_overflow.js")
ANCHOS = (375, 768, 1280)
SITIO = "https://piezas.elur.es"

# Marcadores de plantilla que no pueden llegar a publicarse.
MARCADORES = ("[FALTA", "[GRÁFICO", "[GRAFICO", "PEGAR", "AQUÍ]", "AQUI]",
              "lorem", "LOREM", "TODO:", "XXX", "«PENDIENTE»")

# Prefijos de clase que delimitan un gráfico en este repo. Salen de leer las
# doce piezas, no de inventarlos.
PREFIJOS_GRAFICO = ("figure", "fig-", "chart", "dash", "cmp", "noe", "tl-",
                    "map-", "quiz", "calc", "phos", "panel", "mrow", "sankey")

# Emparejador de cifras. Rechaza la continuación numérica y NADA MÁS.
# Un punto de final de frase no es continuación («caduca en 1997.» casa);
# un dígito detrás sí lo es («211,4» no casa dentro de «211,49»).
# El signo delante tampoco estorba: el repo escribe las subidas como «+146%».
_ANTES = r'(?<!\d)(?<![\d][.,])'
_DESP = r'(?!\d)(?![.,]\d)'


def norm(s):
    s = str(s).replace("−", "-").replace("\u00a0", " ").replace("\u202f", " ")
    return " ".join(s.split())


def aparece(valor, texto):
    v = norm(valor)
    if not v:
        return True
    return re.search(_ANTES + re.escape(v) + _DESP, texto) is not None


def significativa(valor):
    """¿Se le puede exigir algo a esta cifra?

    Regla de la casa (CLAUDE.md:449-450): a las de un solo dígito no. Un «0» o
    un «2» casan en cualquier tabla y en cualquier coordenada de un SVG.
    """
    return len(re.sub(r"\D", "", norm(valor))) >= 2


def es_grafico(tag, attrs):
    if tag in ("figure", "svg"):
        return True
    return any(c.startswith(PREFIJOS_GRAFICO)
               for c in (attrs.get("class") or "").split())


# ───────────────────────────── contexto ─────────────────────────────

class Pieza(object):
    def __init__(self, repo, slug):
        self.repo = repo
        self.slug = slug
        self.dir = os.path.join(repo, slug)
        self.ruta_es = os.path.join(self.dir, "index.html")
        self.ruta_en = os.path.join(self.dir, "en", "index.html")
        self.ruta_datos = os.path.join(self.dir, "datos.json")

    def leer(self, ruta):
        try:
            with open(ruta, encoding="utf-8") as f:
                return f.read()
        except IOError:
            return ""

    @property
    def es(self):
        return self.leer(self.ruta_es)

    @property
    def en(self):
        return self.leer(self.ruta_en)

    @property
    def datos(self):
        try:
            with open(self.ruta_datos, encoding="utf-8") as f:
                return json.load(f)
        except (IOError, ValueError):
            return {}

    def raiz(self, nombre):
        return self.leer(os.path.join(self.repo, nombre))

    def ediciones(self):
        return [("es", self.ruta_es, self.es), ("en", self.ruta_en, self.en)]


# ───────────────────────── familias sin navegador ─────────────────────────

def fam_plantilla(p):
    """Ningún marcador de plantilla impreso."""
    fallos = []
    for idioma, ruta, doc in p.ediciones():
        if not doc:
            continue
        visible = arbol.sin_marcas(re.sub(r"<head.*?</head>", " ", doc, flags=re.S | re.I))
        for m in MARCADORES:
            if m in visible or m in doc:
                donde = doc.find(m)
                linea = doc[:donde].count("\n") + 1 if donde >= 0 else 0
                fallos.append("[%s] marcador de plantilla «%s» en %s:%d"
                              % (idioma, m, os.path.relpath(ruta, p.repo), linea))
    return fallos


def fam_svg_var(p):
    """Ningún var() dentro de fill= o stroke= de un SVG.

    En Safari un fill inválido cae a negro y el stroke a none: el gráfico
    desaparece sin que nadie se entere (CLAUDE.md:217-218).
    """
    fallos = []
    for idioma, ruta, doc in p.ediciones():
        for m in re.finditer(r'(fill|stroke)\s*=\s*"([^"]*var\([^"]*)"', doc, re.I):
            linea = doc[:m.start()].count("\n") + 1
            fallos.append('[%s] %s="%s" en %s:%d — en Safari esto no se ve'
                          % (idioma, m.group(1), m.group(2), os.path.relpath(ruta, p.repo), linea))

        # Un <svg> sin viewBox no escala: en móvil se recorta y no hay forma de
        # ver el trozo que falta. Es la gotcha 3 del manual («min-width:0 en los
        # SVG que deban caber en móvil»), y las catorce del repo lo cumplen hoy,
        # así que esto es un trinquete: que la número quince no se caiga.
        for m in re.finditer(r"<svg\b([^>]*)>", doc, re.I):
            if "viewbox" not in m.group(1).lower():
                linea = doc[:m.start()].count("\n") + 1
                fallos.append("[%s] <svg> sin viewBox en %s:%d — no escala, y en "
                              "móvil se recorta sin aviso"
                              % (idioma, os.path.relpath(ruta, p.repo), linea))
    return fallos


def _meta(doc, atributo, valor):
    m = re.search(r'<meta[^>]*%s=["\']%s["\'][^>]*content=["\'](.*?)["\']'
                  % (atributo, re.escape(valor)), doc, re.S | re.I)
    if not m:
        m = re.search(r'<meta[^>]*content=["\'](.*?)["\'][^>]*%s=["\']%s["\']'
                      % (atributo, re.escape(valor)), doc, re.S | re.I)
    return norm(m.group(1)) if m else ""


def fam_seo(p):
    """SEO completo en las dos ediciones."""
    fallos = []
    for idioma, ruta, doc in p.ediciones():
        rel = os.path.relpath(ruta, p.repo)
        if not doc:
            fallos.append("[%s] no existe %s" % (idioma, rel))
            continue

        m = re.search(r'<html[^>]*lang=["\']([^"\']+)["\']', doc, re.I)
        if not m:
            fallos.append("[%s] falta lang en <html> (%s)" % (idioma, rel))
        elif not m.group(1).lower().startswith(idioma):
            fallos.append('[%s] lang="%s" y debería empezar por "%s" (%s)'
                          % (idioma, m.group(1), idioma, rel))

        t = re.search(r"<title>(.*?)</title>", doc, re.S | re.I)
        if not t or not norm(t.group(1)):
            fallos.append("[%s] <title> vacío o ausente (%s)" % (idioma, rel))

        desc = _meta(doc, "name", "description")
        if not desc:
            fallos.append("[%s] falta meta description (%s)" % (idioma, rel))
        elif len(desc) > 158:
            fallos.append("[%s] meta description de %d caracteres, el tope son 158 (%s)"
                          % (idioma, len(desc), rel))

        can = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', doc, re.I)
        esperado = "%s/%s/%s" % (SITIO, p.slug, "en/" if idioma == "en" else "")
        esperado = esperado.replace("//en/", "/en/")
        if not can:
            fallos.append("[%s] falta canonical (%s)" % (idioma, rel))
        elif can.group(1).rstrip("/") + "/" != esperado.rstrip("/") + "/":
            fallos.append('[%s] canonical dice «%s» y la pieza vive en «%s» (%s)'
                          % (idioma, can.group(1), esperado, rel))

        for prop in ("og:type", "og:title", "og:description", "og:url", "og:image"):
            if not _meta(doc, "property", prop):
                fallos.append("[%s] falta %s (%s)" % (idioma, prop, rel))
        for nom in ("twitter:card", "twitter:title", "twitter:description", "twitter:image"):
            if not _meta(doc, "name", nom):
                fallos.append("[%s] falta %s (%s)" % (idioma, nom, rel))

        # og:image tiene que existir de verdad, ser un JPEG y no estar vacío.
        # Se comprueba el fichero, no una petición de red: estas piezas se
        # verifican antes de publicarse, cuando la URL todavía no responde.
        img = _meta(doc, "property", "og:image")
        if img:
            if not img.startswith(SITIO):
                fallos.append("[%s] og:image apunta fuera del sitio: %s" % (idioma, img))
            else:
                local = os.path.join(p.repo, img[len(SITIO):].lstrip("/"))
                if not os.path.isfile(local):
                    fallos.append("[%s] og:image «%s» no existe en el repo (%s)"
                                  % (idioma, img, os.path.relpath(local, p.repo)))
                else:
                    with open(local, "rb") as f:
                        cab = f.read(3)
                    if cab != b"\xff\xd8\xff":
                        fallos.append("[%s] og:image no es un JPEG: %s" % (idioma, img))
                    elif os.path.getsize(local) < 8192:
                        fallos.append("[%s] og:image pesa %d bytes, está vacía o rota: %s"
                                      % (idioma, os.path.getsize(local), img))
                    if idioma == "en" and "-en" not in os.path.basename(local):
                        fallos.append("[en] og:image es la portada española: %s" % img)

        bloques = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                             doc, re.S | re.I)
        if not bloques:
            fallos.append("[%s] falta el JSON-LD (%s)" % (idioma, rel))
        for b in bloques:
            try:
                d = json.loads(b)
            except ValueError as e:
                fallos.append("[%s] el JSON-LD no parsea: %s (%s)" % (idioma, e, rel))
                continue
            tipos = [d.get("@type")] if isinstance(d, dict) else []
            if "Article" in tipos and not d.get("dateModified"):
                fallos.append("[%s] el JSON-LD Article no lleva dateModified (%s)" % (idioma, rel))
    return fallos


def fam_alta(p):
    """Alta en sitemap.xml y en las dos portadas."""
    fallos = []
    sm = p.raiz("sitemap.xml")
    if not sm:
        fallos.append("no se encuentra sitemap.xml")
    else:
        for url in ("%s/%s/" % (SITIO, p.slug), "%s/%s/en/" % (SITIO, p.slug)):
            if "<loc>%s</loc>" % url not in sm:
                fallos.append("sitemap.xml no da de alta %s" % url)

    portada = p.raiz("index.html")
    if not portada:
        fallos.append("no se encuentra index.html")
    elif 'href="%s/"' % p.slug not in portada:
        fallos.append('la portada española no enlaza la pieza (falta href="%s/")' % p.slug)

    portada_en = p.raiz(os.path.join("en", "index.html"))
    if not portada_en:
        fallos.append("no se encuentra en/index.html")
    elif 'href="../%s/en/"' % p.slug not in portada_en:
        fallos.append('la portada inglesa no enlaza la pieza (falta href="../%s/en/")' % p.slug)

    # El ItemList tiene que contar bien y contener la pieza. Que numberOfItems
    # diga 12 con once entradas es invisible a simple vista.
    for nombre, doc, sufijo in (("index.html", portada, ""),
                                ("en/index.html", portada_en, "en/")):
        if not doc:
            continue
        m = re.search(r'"numberOfItems"\s*:\s*(\d+)', doc)
        items = re.findall(r'"@type"\s*:\s*"ListItem"', doc)
        if m and int(m.group(1)) != len(items):
            fallos.append("%s: numberOfItems dice %s y hay %d ListItem"
                          % (nombre, m.group(1), len(items)))
        if items and ('"%s/%s/%s"' % (SITIO, p.slug, sufijo)) not in doc:
            fallos.append("%s: la pieza no está en el ItemList" % nombre)
    return fallos


def fam_grafico(p):
    """Ninguna cifra del texto contradice a su gráfico.

    Versión comprobable: toda cifra que el manifiesto declara publicada en
    `graficos` tiene que estar DENTRO de un gráfico. Es lo que caza el error
    que más ha costado aquí — el número corregido en el cuerpo y no en la
    figura, como el «300%» de Argentina que siguió tres días en su portada.

    Lo que NO se comprueba, y se dice: si la cifra del gráfico es la correcta.
    Eso lo mira `verificar_datos.py` contra el manifiesto, y que el manifiesto
    diga la verdad lo mira una persona con la fuente abierta.
    """
    fallos = []
    datos = p.datos
    if not datos:
        return ["no hay datos.json: la pieza no declara ninguna cifra"]
    doc = p.es
    graf = arbol.sin_marcas(" ".join(arbol.regiones(doc, es_grafico)))
    graf += " " + norm(" ".join(re.findall(r'data-(?:count|metric)="([^"]+)"', doc)))
    for clave, e in (datos.get("cifras") or {}).items():
        if e.get("retirado"):
            continue
        valor = str(e.get("valor", ""))
        if not significativa(valor):
            continue
        if "graficos" in (e.get("superficies") or []) and not aparece(valor, graf):
            fallos.append("«%s» (%s) se declara publicada en un gráfico y no está "
                          "en ninguno: el gráfico y el manifiesto no dicen lo mismo"
                          % (valor, clave))
    return fallos


def _a_ingles(v):
    """1.093,5 → 1,093.5"""
    return norm(v).replace(".", "\x00").replace(",", ".").replace("\x00", ",")


def fam_bilingue(p):
    """Coherencia entre las dos ediciones: toda cifra declarada vive en las dos.

    Se recorre el manifiesto en los DOS sentidos: la cifra tiene que estar en
    la española y en la inglesa, cada una con el formato de su idioma
    (1.093,5 aquí, 1,093.5 allí).

    LO QUE NO SE COMPRUEBA, Y POR QUÉ NO SE PUEDE
    La primera versión barría además TODAS las cifras del texto inglés y exigía
    su equivalente español. Saltó a la primera sobre `casio-encogerse`, que está
    bien: el castellano dice «1.500 millones de euros» y el inglés «1.5 billion
    euros». Misma magnitud, palabra de escala distinta. No es un fallo de
    formato, es que los dos idiomas cuentan en escalas distintas, y ninguna
    conversión de separadores lo arregla.

    Así que ese barrido se retira en vez de dejarlo gritando. Lo que queda es
    exacto. Y lo que sí hay que mirar con ojos —si el inglés introduce una cifra
    que el castellano no da— queda como pregunta a una persona en la skill de
    cierre, no como un rojo que nadie se creería.
    """
    fallos = []
    es, en = p.es, p.en
    if not en:
        return ["no existe la edición inglesa"]

    def cuerpo(doc):
        d = re.sub(r"<head.*?</head>", " ", doc, flags=re.S | re.I)
        d = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", d, flags=re.S | re.I)
        return arbol.sin_marcas(d)

    t_es, t_en = cuerpo(es), cuerpo(en)
    for clave, e in (p.datos.get("cifras") or {}).items():
        if e.get("retirado"):
            continue
        v = str(e.get("valor", ""))
        if not significativa(v):
            continue
        # Un `valor` puede ser una frase con fecha —«5 de agosto de 2026»— y
        # entonces la edición inglesa dice «5 August 2026». Eso es traducción,
        # no formato de número, y ninguna conversión de separadores lo salva:
        # la comprobación daba rojo en narcolepsia-orexina y tim-cook-apple con
        # las dos ediciones correctas. Que la fecha esté bien traducida lo mira
        # `verificar_en.py`, que sí sabe de fechas.
        if re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", v):
            continue
        sup = e.get("superficies") or []
        if not any(s in sup for s in ("cuerpo", "graficos", "dek", "titulo")):
            continue
        en_es = aparece(v, t_es)
        en_en = aparece(_a_ingles(v), t_en) or aparece(v, t_en)
        if en_es and not en_en:
            fallos.append("«%s» (%s) está en la edición española y no en la inglesa "
                          "(ni como «%s»)" % (v, clave, _a_ingles(v)))
        elif en_en and not en_es:
            fallos.append("«%s» (%s) está en la edición inglesa y no en la española"
                          % (v, clave))
    return fallos



# ───────────────────────── retiradas y cronología ─────────────────────────

# Las marcas con las que este repo declara que algo se retira o se corrige.
# Salen de leer las 39 notas que ya existen en las doce piezas, no de inventarlas.
MARCA_RETIRADA = re.compile(
    r"(Correcci[óo]n|Rectificaci[óo]n|Dato retirado|Hueco declarado|Se retira"
    r"|Correction|Declared gap|Data withdrawn|Withdrawn)", re.I)

DEUDA_RETIRADAS = "retiradas_sin_declarar.json"


def _notas_de_correccion(doc):
    """Los bloques de texto que declaran una corrección o una retirada."""
    fuera = []
    for r in arbol.regiones(doc, lambda t, a: t in ("p", "div", "li", "figcaption")):
        t = arbol.sin_marcas(r)
        if MARCA_RETIRADA.search(t):
            fuera.append(t)
    return fuera


def fam_retirada(p):
    """Una pieza no puede publicar en un sitio lo que retira en otro.

    QUÉ HACE ESTO Y QUÉ NO, PORQUE LA DIFERENCIA IMPORTA

    La vigilancia —que una cifra marcada `retirado` no siga viva en ninguna
    superficie— YA EXISTE y funciona: `verificar_datos.py:275-290` borra las
    notas de corrección (para que la nota pueda citar lo que retiró) y luego
    busca el valor en las catorce superficies. El gate ya lo invoca.

    El agujero no es la vigilancia: es la DECLARACIÓN. En las doce piezas hay
    **39 notas de corrección y 8 retiradas declaradas**. Lo que no se declara
    es invisible para el comprobador, exactamente igual que pasaba con las
    cifras (74 declaradas frente a 235 sin declarar).

    POR QUÉ NO SE EXTRAE LA CIFRA RETIRADA DE LA PROSA
    Se probó. La versión que saca toda cifra de la nota y exige que esté muerta
    fuera marca **345 zombis** sobre doce piezas que hoy se dan por correctas.
    El motivo es que la nota contiene A LA VEZ lo que se retiró y lo que se
    corrigió: en `argentina-milei`, «daba antes … agua 365%, luz 339%» y «da
    estas variaciones: gas natural 2.071%, transporte 1.442%» viven en el mismo
    párrafo, y las segundas TIENEN que seguir vivas. El caso que lo cierra está
    en `caida-gopro`: «pasa de 0,60 a 0,61 dólares —Nasdaq da 0,6084 ese día;
    el 0,60 era el cierre del 24—». Ahí «0,60» está retirado como precio del 25
    y es cierto como cierre del 24, en la misma frase. Ninguna expresión regular
    ni análisis de tiempos verbales separa eso, y un detector que salta 345
    veces sobre material correcto no lo usaría nadie dos veces.

    Así que lo que se automatiza es lo que se puede automatizar sin mentir:
    quien escribe la corrección dice qué retira —que es lo que sabe— y la
    máquina se encarga de que no se le olvide y de que no vuelva a aparecer.
    """
    fallos = []

    # ── 1 · cronología: los hitos van en orden, y eso sí es mecánico ──
    #
    # Cubre la mitad del caso que motivó esta familia: una corrección que mueve
    # un hito «después del foro de Doha, no antes». Si el hito se redata y no se
    # recoloca, o al revés, las fechas dejan de ser monótonas y se ve sin leer
    # una palabra de prosa.
    for idioma, ruta, doc in p.ediciones():
        if not doc:
            continue
        fechas = re.findall(r'data-(?:date|fecha)="(\d{4}-\d{2}-\d{2})"', doc)
        if len(fechas) < 2:
            continue
        asc = all(fechas[i] <= fechas[i + 1] for i in range(len(fechas) - 1))
        desc = all(fechas[i] >= fechas[i + 1] for i in range(len(fechas) - 1))
        if not (asc or desc):
            saltos = ["%s → %s" % (fechas[i], fechas[i + 1])
                      for i in range(len(fechas) - 1) if fechas[i] > fechas[i + 1]]
            fallos.append("[%s] la cronología no va en orden: %s. Un hito redatado "
                          "y no recolocado (o al revés) deja la serie así"
                          % (idioma, "; ".join(saltos[:3])))

    # ── 2 · trinquete: toda nota nueva declara qué retira ──
    notas = len(_notas_de_correccion(p.es))
    declaradas = len([1 for e in (p.datos.get("cifras") or {}).values()
                      if e.get("retirado")])
    deficit = max(0, notas - declaradas)

    ruta_deuda = os.path.join(p.repo, "herramientas", DEUDA_RETIRADAS)
    try:
        with open(ruta_deuda, encoding="utf-8") as f:
            suelo = json.load(f)
    except (IOError, ValueError):
        suelo = {}

    previo = suelo.get(p.slug)
    if previo is None:
        # Primera vez que se mira esta pieza: se fija el suelo donde esté. Como
        # el trinquete de `sin_declarar.json`, que ya funciona: exigir las 31
        # declaraciones de golpe produciría 31 declaraciones rellenadas a
        # desgana, que es peor que no tenerlas.
        suelo[p.slug] = deficit
    elif deficit > previo:
        fallos.append("hay %d nota(s) de corrección y %d retirada(s) declarada(s) en "
                      "datos.json: la deuda sube de %d a %d. Toda nota nueva declara "
                      "qué retira, o `verificar_datos.py` no puede vigilar que esa "
                      "cifra no reviva en otra superficie"
                      % (notas, declaradas, previo, deficit))
    elif deficit < previo:
        suelo[p.slug] = deficit          # el suelo solo baja

    if suelo.get(p.slug) != previo:
        try:
            os.makedirs(os.path.dirname(ruta_deuda), exist_ok=True)
            with open(ruta_deuda, "w", encoding="utf-8") as f:
                json.dump(suelo, f, ensure_ascii=False, indent=1, sort_keys=True)
        except IOError:
            pass                          # sin permiso de escritura: no se bloquea

    return fallos


# ───────────────────────── familias con navegador ─────────────────────────

class SinNavegador(Exception):
    pass


# El demonio de agent-browser se satura si se le habla desde varios sitios a
# la vez y devuelve «Resource temporarily unavailable». Es pasajero y no es un
# fallo de la pieza, así que se reintenta. Lo que NO se hace es tragárselo: si
# después de los reintentos sigue sin contestar, esto sale con 2 y lo dice.
_TRANSITORIOS = ("temporarily unavailable", "daemon may be busy",
                 "Failed to read", "ECONNREFUSED", "EPIPE")


def _ab(*args):
    ultimo = ""
    for intento in range(4):
        try:
            r = subprocess.run(["agent-browser"] + list(args) + ["--json"],
                               capture_output=True, text=True, timeout=300)
        except (OSError, subprocess.TimeoutExpired) as e:
            ultimo = str(e)
        else:
            salida = (r.stdout or "") + (r.stderr or "")
            if not any(t in salida for t in _TRANSITORIOS):
                return r
            ultimo = salida[:200]
        time.sleep(1.5 * (intento + 1))
    raise SinNavegador("el navegador no responde tras 4 intentos: %s" % ultimo)


def hay_navegador():
    return shutil.which("agent-browser") is not None


def _sonda(url, ancho):
    _ab("open", url)
    _ab("set", "viewport", str(ancho), "900")
    with open(SONDA, encoding="utf-8") as f:
        js = f.read()
    r = _ab("eval", js)
    try:
        return json.loads(json.loads(r.stdout)["data"]["result"])
    except (ValueError, KeyError, TypeError):
        raise SinNavegador("la sonda no devolvió nada legible: %s" % r.stdout[:300])


def fam_overflow(p):
    """Cero desbordamiento horizontal a 375, 768 y 1280."""
    fallos = []
    for idioma, ruta, doc in p.ediciones():
        if not doc:
            continue
        url = "file://" + os.path.abspath(ruta)
        for ancho in ANCHOS:
            o = _sonda(url, ancho)
            for c in o["culpables"]:
                fallos.append("[%s] a %dpx desborda %s: %s (+%spx)"
                              % (idioma, ancho, c["que"], c["motivo"], c["exceso"]))
    return fallos


def _copia_sin_js(ruta, destino):
    """Copia del documento sin los <script src> ni los <script> de conducta.

    El JSON-LD se queda: es un script por la etiqueta, no por lo que hace, y
    quitarlo convertiría esta comprobación en un falso rojo de SEO.
    """
    with open(ruta, encoding="utf-8") as f:
        doc = f.read()
    doc = re.sub(r'<script[^>]*\ssrc=[^>]*>\s*</script>', "", doc, flags=re.I)
    def fuera(m):
        return m.group(0) if "ld+json" in (m.group(1) or "") else ""
    doc = re.sub(r'<script([^>]*)>.*?</script>', fuera, doc, flags=re.S | re.I)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(doc)
    return destino


JS_SIN_JS = r"""(function(){
  var out={svgs:0,svgs_visibles:0,controles_visibles:[],texto:0};
  var vis=function(el){var r=el.getBoundingClientRect();
    var cs=getComputedStyle(el);
    return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'&&cs.opacity!=='0';};
  var svgs=document.querySelectorAll('svg');
  out.svgs=svgs.length;
  for(var i=0;i<svgs.length;i++){if(vis(svgs[i]))out.svgs_visibles++;}
  var n=document.querySelectorAll('.needs-js');
  for(var j=0;j<n.length;j++){
    if(vis(n[j])){
      var el=n[j],s=el.tagName.toLowerCase();
      if(el.id)s+='#'+el.id;
      if(typeof el.className==='string')s+='.'+el.className.trim().split(/\s+/).slice(0,2).join('.');
      out.controles_visibles.push(s);
    }
  }
  out.controles_visibles=out.controles_visibles.slice(0,8);
  out.texto=(document.body.innerText||'').replace(/\s+/g,' ').trim().length;
  return JSON.stringify(out);})()"""


def fam_sin_js(p):
    """La pieza se lee entera sin JavaScript.

    Se genera una copia sin los <script src>, se abre, y se exige que:
      · los gráficos SVG sigan viéndose (el DOM ya muestra el estado final),
      · TODO lo marcado .needs-js esté oculto — si un control interactivo se ve
        sin JS, el lector lo pulsa y no pasa nada,
      · quede texto de verdad, no una página en blanco.

    La copia va a un directorio temporal con `assets/` enlazado, no copiado: el
    CSS carga por ruta relativa y no se escribe ni un byte en el repo. Este
    guion no toca nunca lo que verifica.
    """
    fallos = []
    tmp = tempfile.mkdtemp(prefix="verifica-sinjs-")
    try:
        try:
            os.symlink(os.path.join(p.repo, "assets"), os.path.join(tmp, "assets"))
        except OSError:
            shutil.copytree(os.path.join(p.repo, "assets"), os.path.join(tmp, "assets"))

        for idioma, ruta, doc in p.ediciones():
            if not doc:
                continue
            rel = os.path.relpath(ruta, p.repo)
            destino = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            _copia_sin_js(ruta, destino)

            _ab("open", "file://" + destino)
            _ab("set", "viewport", "375", "900")
            r = _ab("eval", JS_SIN_JS)
            try:
                o = json.loads(json.loads(r.stdout)["data"]["result"])
            except (ValueError, KeyError, TypeError):
                raise SinNavegador("sin lectura de la copia sin JS: %s" % r.stdout[:300])

            con_svg = len(re.findall(r"<svg", doc, re.I))
            if con_svg and o["svgs_visibles"] < con_svg:
                fallos.append("[%s] sin JS se ven %d de %d gráficos SVG: la pieza "
                              "no se lee entera" % (idioma, o["svgs_visibles"], con_svg))
            for c in o["controles_visibles"]:
                fallos.append("[%s] sin JS se ve el control «%s», que no hace nada. "
                              "Falta la regla #pieza .needs-js{display:none}" % (idioma, c))
            if o["texto"] < 800:
                fallos.append("[%s] sin JS la página deja %d caracteres de texto: "
                              "está en blanco" % (idioma, o["texto"]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return fallos


# ───────────────────────── las herramientas del repo ─────────────────────────

EXTERNAS = (
    ("verificar_datos.py", True),        # acepta el slug
    ("coherencia_metadatos.py", True),
    ("verificar_en.py", True),
    ("deriva_tarjeta.py", True),
)


def fam_externos(p):
    """Los cuatro verificadores que ya existen. Verde solo si todos dan verde."""
    fallos = []
    herr = os.path.join(p.repo, "herramientas")
    for nombre, acepta_slug in EXTERNAS:
        ruta = os.path.join(herr, nombre)
        if not os.path.isfile(ruta):
            raise SinNavegador("falta herramientas/%s: la báscula está incompleta" % nombre)
        cmd = [sys.executable, ruta] + ([p.slug] if acepta_slug else [])
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=p.repo, timeout=600)
        if r.returncode != 0:
            cola = [l for l in (r.stdout or "").splitlines() if l.strip()][-6:]
            fallos.append("%s sale con %d:\n      %s"
                          % (nombre, r.returncode, "\n      ".join(cola)))
    return fallos


# ───────────────────────────── el control positivo ─────────────────────────────

def _inyecta(ruta, fragmento):
    with open(ruta, encoding="utf-8") as f:
        doc = f.read()
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(doc.replace("</body>", fragmento + "</body>", 1))


def rotura_plantilla(p):
    _inyecta(p.ruta_es, '<p>[FALTA la cifra de cierre]</p>')


def rotura_svg_var(p):
    _inyecta(p.ruta_es, '<svg viewBox="0 0 10 10" width="10" height="10">'
                        '<rect width="10" height="10" fill="var(--accent)"/></svg>')


def rotura_svg_viewbox(p):
    _inyecta(p.ruta_es, '<svg width="10" height="10">'
                        '<rect width="10" height="10" fill="#000"/></svg>')


def rotura_seo(p):
    with open(p.ruta_es, encoding="utf-8") as f:
        doc = f.read()
    doc = re.sub(r'<link[^>]*rel=["\']canonical["\'][^>]*>', "", doc, count=1, flags=re.I)
    with open(p.ruta_es, "w", encoding="utf-8") as f:
        f.write(doc)


def rotura_alta(p):
    ruta = os.path.join(p.repo, "sitemap.xml")
    with open(ruta, encoding="utf-8") as f:
        sm = f.read()
    sm = sm.replace("<loc>%s/%s/</loc>" % (SITIO, p.slug), "<loc>%s/NO-EXISTE/</loc>" % SITIO, 1)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(sm)


def rotura_grafico(p):
    """Le quita al gráfico una cifra que el manifiesto declara dibujada.

    Es el «300%» de Argentina: corregido en el cuerpo, intacto en la figura.

    Si la pieza no tiene ninguna cifra con la que romper —`casio-encogerse` solo
    declara en gráficos un «7», y a las de un dígito no se les exige— se declara
    una cifra nueva en el manifiesto que ningún gráfico dibuja. La rotura tiene
    que poder construirse SIEMPRE: un control que se salta a sí mismo cuando la
    pieza no se deja no es un control.
    """
    datos = p.datos
    with open(p.ruta_es, encoding="utf-8") as f:
        doc = f.read()
    for clave, e in (datos.get("cifras") or {}).items():
        if e.get("retirado") or "graficos" not in (e.get("superficies") or []):
            continue
        v = norm(str(e.get("valor", "")))
        if not significativa(v):
            continue
        for r in arbol.regiones(doc, es_grafico):
            if v in r:
                nuevo = doc.replace(r, r.replace(v, v + "9"), 1)
                if nuevo != doc:
                    with open(p.ruta_es, "w", encoding="utf-8") as f:
                        f.write(nuevo)
                    return True
    # Reserva: una cifra declarada en gráficos que no dibuja nadie.
    datos.setdefault("cifras", {})["control_positivo"] = {
        "valor": "48.271", "unidad": "control", "periodo": "control",
        "fuente": "control positivo", "url": "https://example.invalid",
        "consultado": "2026-09-06", "tipo": "ESTABLE", "derivado": False,
        "superficies": ["graficos"],
    }
    with open(p.ruta_datos, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return True


def rotura_bilingue(p):
    """Le cambia a la edición inglesa una cifra que el manifiesto declara.

    La rotura tiene que atacar lo que la familia mira. La primera versión metía
    una cifra suelta en el inglés y funcionaba contra el barrido libre; al
    retirarse ese barrido —porque «1.500 millones» y «1.5 billion» no se pueden
    comparar sin semántica— la rotura dejó de tocar nada y el control lo cazó.
    Ahora rompe lo que de verdad se comprueba: una cifra declarada deja de
    estar en la inglesa.
    """
    with open(p.ruta_en, encoding="utf-8") as f:
        doc = f.read()
    for clave, e in (p.datos.get("cifras") or {}).items():
        if e.get("retirado"):
            continue
        v = str(e.get("valor", ""))
        if not significativa(v):
            continue
        sup = e.get("superficies") or []
        if not any(x in sup for x in ("cuerpo", "graficos", "dek", "titulo")):
            continue
        for candidata in (_a_ingles(v), norm(v)):
            if candidata in doc:
                # TODAS las apariciones, no la primera. La primera suele estar
                # en el <head>, y la comprobación mira el cuerpo: rompiendo solo
                # el metadato, el control se quedaba sin efecto y decía que la
                # familia no saltaba.
                with open(p.ruta_en, "w", encoding="utf-8") as f:
                    f.write(doc.replace(candidata, candidata + "9"))
                return True
    return False


def rotura_overflow(p):
    _inyecta(p.ruta_es, '<div style="width:1400px;height:24px">control positivo</div>')


def rotura_sin_js(p):
    """Le quita a la pieza la regla que oculta los controles sin JavaScript.

    Reproduce el fallo que de verdad puede ocurrir: una pieza nueva que se
    escribe sin cargar `assets/interactives.css` —o a la que se le borra el
    bloque `.needs-js{display:none}`— publica sus botones a la vista sin JS. El
    lector los pulsa y no pasa nada.

    LA VERSIÓN ANTERIOR DE ESTA ROTURA YA NO VALÍA, Y ESO ES UNA BUENA NOTICIA
    Antes inyectaba un `<button class="needs-js">` FUERA de la raíz de la pieza,
    donde la regla copiada a mano `#pieza .needs-js{display:none}` no llegaba.
    Contra `argentina-milei` migrada dejó de saltar: la regla global de
    interactives.css sí cubre lo que está fuera de la raíz, así que la librería
    tapó el agujero que la rotura explotaba. El control lo detectó y avisó en
    vez de dar por buena una comprobación que ya no probaba nada.

    Se inyecta además un control propio, para que la rotura pueda construirse
    también en las piezas que no tienen ninguno.
    """
    _inyecta(p.ruta_es, '<button class="needs-js" id="control-positivo">pulsa</button>')
    with open(p.ruta_es, encoding="utf-8") as f:
        doc = f.read()
    doc = re.sub(r'<link[^>]*interactives\.css[^>]*>', "", doc, flags=re.I)
    doc = re.sub(r'[^\n{}]*\.needs-js\s*\{[^}]*display\s*:\s*none[^}]*\}', "", doc, flags=re.I)
    with open(p.ruta_es, "w", encoding="utf-8") as f:
        f.write(doc)


# (etiqueta del control, familia que tiene que saltar, cómo se rompe)
# Una familia puede llevar varios controles: la de SVG mira dos cosas distintas
# —el var() invisible en Safari y el viewBox que falta— y cada una necesita su
# propia rotura. Con una sola, la otra comprobación viajaría sin probar.

def rotura_cronologia(p):
    """Redata un hito hacia atrás sin recolocarlo: la serie deja de ser monótona."""
    with open(p.ruta_es, encoding="utf-8") as f:
        doc = f.read()
    fechas = re.findall(r'data-(?:date|fecha)="(\d{4}-\d{2}-\d{2})"', doc)
    if len(fechas) >= 2:
        # el último hito pasa a ser anterior al primero
        viejo = 'data-date="%s"' % fechas[-1]
        if viejo not in doc:
            viejo = 'data-fecha="%s"' % fechas[-1]
        nuevo = viejo.replace(fechas[-1], "1999-01-01")
        with open(p.ruta_es, "w", encoding="utf-8") as f:
            f.write(doc.replace(viejo, nuevo, 1))
        return True
    # La pieza no tiene cronología: se le inyecta una desordenada.
    # Tres hitos, no dos: con dos, cualquier orden es ascendente o descendente
    # y la comprobación —que acepta las dos direcciones, porque una cronología
    # puede ir de lo más nuevo a lo más viejo— no tendría nada que decir.
    _inyecta(p.ruta_es, '<ul><li data-date="2024-01-01">a</li>'
                        '<li data-date="2026-05-01">c</li>'
                        '<li data-date="2025-03-01">b</li></ul>')
    return True


def rotura_retirada_sin_declarar(p):
    """Añade una nota de corrección y no declara nada. Es el caso real: la nota
    se escribe, la declaración se olvida, y a partir de ahí nadie vigila que esa
    cifra no reviva en otra superficie."""
    _inyecta(p.ruta_es, '<p><strong>Corrección.</strong> Este panel daba antes '
                        'otra cifra en este punto y se ha rehecho.</p>')


CONTROLES = (
    ("plantilla", "plantilla", rotura_plantilla),
    ("svg · var() en fill", "svg_var", rotura_svg_var),
    ("svg · sin viewBox", "svg_var", rotura_svg_viewbox),
    ("seo", "seo", rotura_seo),
    ("alta", "alta", rotura_alta),
    ("grafico", "grafico", rotura_grafico),
    ("bilingue", "bilingue", rotura_bilingue),
    ("overflow", "overflow", rotura_overflow),
    ("sin_js", "sin_js", rotura_sin_js),
    ("cronología", "retirada", rotura_cronologia),
    ("retirada sin declarar", "retirada", rotura_retirada_sin_declarar),
)

FAMILIAS = (
    ("plantilla", fam_plantilla, False),
    ("svg_var", fam_svg_var, False),
    ("seo", fam_seo, False),
    ("alta", fam_alta, False),
    ("grafico", fam_grafico, False),
    ("bilingue", fam_bilingue, False),
    ("retirada", fam_retirada, False),
    ("overflow", fam_overflow, True),
    ("sin_js", fam_sin_js, True),
    ("externos", fam_externos, False),
)


def control_positivo(repo, slug, con_render, verboso=True):
    """Rompe una copia a propósito y exige que suene POR LA ROTURA.

    NO BASTA CON QUE LA COMPROBACIÓN DEVUELVA ALGO
    La primera versión de este control daba por buena cualquier familia que
    devolviera un fallo tras la rotura. Se coló al primer intento: la familia
    `bilingue` tenía un falso positivo propio sobre la pieza intacta —el
    castellano dice «1.500 millones» y el inglés «1.5 billion»— así que
    «saltaba» siempre, con rotura y sin ella. El control la daba por buena y
    en realidad no estaba probando nada.

    Así que se mide dos veces: la copia limpia y la copia rota. La rotura tiene
    que producir un fallo NUEVO. Si los dos conjuntos son iguales, la familia no
    ha detectado la rotura, por mucho que esté gritando otra cosa.
    """
    rotas = []
    funcs = dict((n, f) for n, f, _ in FAMILIAS)
    necesita = dict((n, r) for n, _, r in FAMILIAS)
    for etiqueta, nombre, romper in CONTROLES:
        if necesita[nombre] and not con_render:
            continue
        tmp = tempfile.mkdtemp(prefix="verifica-control-")
        try:
            limpio = os.path.join(tmp, "limpio")
            roto = os.path.join(tmp, "roto")
            shutil.copytree(repo, limpio, ignore=shutil.ignore_patterns(".git"))
            shutil.copytree(repo, roto, ignore=shutil.ignore_patterns(".git"))

            antes = set(funcs[nombre](Pieza(limpio, slug)))

            # Algunas familias llevan trinquete y escriben su suelo en
            # herramientas/*.json la primera vez que ven una pieza. Sin
            # trasladar ese suelo a la copia rota, la rotura también sería «la
            # primera vez» y el trinquete se limitaría a fijar el listón más
            # alto en vez de sonar. El control lo detectó: la deuda de
            # retiradas no saltaba nunca.
            herr_l = os.path.join(limpio, "herramientas")
            herr_r = os.path.join(roto, "herramientas")
            if os.path.isdir(herr_l) and os.path.isdir(herr_r):
                for j in os.listdir(herr_l):
                    if j.endswith(".json"):
                        shutil.copy2(os.path.join(herr_l, j), os.path.join(herr_r, j))

            pr = Pieza(roto, slug)
            if romper(pr) is False:
                rotas.append("%s: no se pudo construir la rotura" % etiqueta)
                continue
            despues = set(funcs[nombre](pr))

            nuevos = despues - antes
            if not nuevos:
                if antes:
                    rotas.append("%s: se rompió la copia a propósito y NO apareció "
                                 "ningún fallo nuevo. La familia ya gritaba %d cosa(s) "
                                 "antes de romper nada, así que no está detectando la "
                                 "rotura: está detectando un falso positivo suyo. "
                                 "Primero: %s" % (etiqueta, len(antes), sorted(antes)[0][:90]))
                else:
                    rotas.append("%s: se rompió la copia a propósito y la comprobación "
                                 "NO saltó" % etiqueta)
            elif verboso:
                print("      · %-20s salta ✓  (%s)" % (etiqueta, sorted(nuevos)[0][:66]))
        except SinNavegador as e:
            rotas.append("%s: %s" % (etiqueta, e))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # Las herramientas del repo traen su propio control positivo. Se corre.
    externas_caidas = []
    for nombre in ("verificar_datos.py", "verificar_en.py"):
        ruta = os.path.join(repo, "herramientas", nombre)
        if not os.path.isfile(ruta):
            rotas.append("externos: falta herramientas/%s" % nombre)
            continue
        try:
            r = subprocess.run([sys.executable, ruta, "--autotest"],
                               capture_output=True, text=True, cwd=repo, timeout=600)
        except (OSError, subprocess.TimeoutExpired) as e:
            rotas.append("externos: %s --autotest no se pudo correr: %s" % (nombre, e))
            continue
        salida = (r.stdout or "")
        fallido = r.returncode != 0 or "CONTROL POSITIVO FALLIDO" in salida
        if fallido:
            externas_caidas.append(nombre)
        elif verboso:
            print("      · %-20s salta ✓  (%s --autotest)" % ("externos", nombre))
    return rotas, externas_caidas


# ───────────────────────────────── principal ─────────────────────────────────

def verifica(repo, slug, con_render):
    p = Pieza(repo, slug)
    res = {}
    for nombre, func, necesita_render in FAMILIAS:
        if necesita_render and not con_render:
            res[nombre] = None
            continue
        try:
            res[nombre] = func(p)
        except SinNavegador as e:
            raise
    return res


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("piezas", nargs="*")
    ap.add_argument("--repo", default=os.path.expanduser("~/Desktop/elur-piezas"))
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--solo-control", action="store_true")
    ap.add_argument("--sin-render", action="store_true",
                    help="no abre el navegador. Sale con 2 aunque todo lo demás pase.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    repo = os.path.abspath(os.path.expanduser(a.repo))
    if not os.path.isdir(repo):
        print("No encuentro el repo en %s" % repo)
        return 2

    slugs = a.piezas
    if a.todas or not slugs:
        slugs = sorted(d for d in os.listdir(repo)
                       if os.path.isfile(os.path.join(repo, d, "datos.json")))
    if not slugs:
        print("No hay piezas que verificar en %s" % repo)
        return 2

    con_render = not a.sin_render
    if con_render and not hay_navegador():
        print("═" * 72)
        print("BÁSCULA ROTA · no encuentro `agent-browser`, y sin él no se puede")
        print("medir el desbordamiento ni comprobar que la pieza se lee sin JS.")
        print("  Instalar:  npm install -g agent-browser")
        print("  O correr:  verifica_pieza.py --sin-render  (sale con 2 igualmente)")
        print("═" * 72)
        return 2

    # ── 1 · el control positivo, siempre y antes de nada ──
    #
    # Se hace sobre una pieza de REFERENCIA, no sobre la que se está mirando.
    # El control compara los fallos antes y después de romper, y una pieza a
    # medio escribir ya grita por su cuenta: el delta se pierde y el control se
    # declara roto cuando lo que está a medias es la pieza. Pasó al probar el
    # esqueleto recién generado por scaffold_pieza.py.
    # La referencia es una pieza publicada que no esté entre las examinadas; si
    # se piden todas, la primera. Sobre ficheros reales, como manda la casa.
    candidatas = sorted(d for d in os.listdir(repo)
                        if os.path.isfile(os.path.join(repo, d, "datos.json"))
                        and os.path.isfile(os.path.join(repo, d, "en", "index.html")))
    fuera = [c for c in candidatas if c not in slugs]
    referencia = (fuera or candidatas or slugs)[0]

    print("═" * 72)
    print("CONTROL POSITIVO · rompiendo una copia de «%s» a propósito" % referencia)
    print("═" * 72)
    try:
        rotas, externas_caidas = control_positivo(repo, referencia, con_render,
                                                  verboso=not a.json)
    except Exception as e:
        print("El control positivo se cayó: %s" % e)
        return 2

    # El `--autotest` de las herramientas del repo se cae también cuando el
    # repo tiene un fallo de datos DE VERDAD: inyecta un error sobre una pieza
    # que ya fallaba y no puede distinguir su inyección del fallo que ya había.
    # Es el mismo agujero que tenía el control de este guion antes de medir el
    # delta. Si su comprobación normal encuentra fallos, lo roto es la pieza y
    # hay que ENSEÑARLOS, no esconderlos detrás de un «báscula rota».
    if externas_caidas:
        # Se mira en las piezas QUE SE ESTÁN EXAMINANDO, no en la de
        # referencia: el fallo real puede estar en cualquiera de ellas y la de
        # referencia se elige precisamente por estar fuera del lote.
        reales = []
        for sl in slugs:
            try:
                reales += fam_externos(Pieza(repo, sl))
            except SinNavegador:
                pass
        if reales:
            print()
            print("AVISO · el --autotest de %s se ha caído, y la comprobación normal"
                  % ", ".join(externas_caidas))
            print("de esas mismas herramientas encuentra fallos reales en el repo. El")
            print("autotest inyecta un error sobre una pieza que YA fallaba y no puede")
            print("distinguir el suyo del que había. Se sigue: lo roto es el contenido.")
            print("Arreglados los fallos de abajo, vuelve a correr esto para probar la")
            print("báscula de verdad.")
        else:
            rotas.append("externos: %s --autotest falla y su comprobación normal está "
                         "limpia. La báscula sí está rota."
                         % ", ".join(externas_caidas))
    if rotas:
        print()
        print("LA BÁSCULA ESTÁ ROTA. No se ha llegado a mirar ninguna pieza.")
        for r in rotas:
            print("  ✗ %s" % r)
        print()
        print("Un verde de un verificador que no puede fallar no significa nada.")
        return 2
    print("      control positivo completo: todas las familias saltan.")
    print()

    if a.solo_control:
        print("VERDE · la báscula funciona. (--solo-control: no se ha mirado ninguna pieza)")
        return 0

    # ── 2 · ahora sí, las piezas ──
    informe = {}
    total = 0
    for slug in slugs:
        try:
            res = verifica(repo, slug, con_render)
        except SinNavegador as e:
            print("BÁSCULA ROTA al verificar %s: %s" % (slug, e))
            return 2
        fallos = [(fam, f) for fam, lst in res.items() if lst for f in lst]
        informe[slug] = dict((k, v) for k, v in res.items())
        total += len(fallos)
        if not a.json:
            print("─" * 72)
            estado = "VERDE" if not fallos else "ROJO · %d" % len(fallos)
            print("%-24s %s" % (slug, estado))
            for fam, f in fallos:
                print("   [%s] %s" % (fam, f))
    if a.json:
        print(json.dumps({"repo": repo, "piezas": informe, "fallos": total},
                         ensure_ascii=False, indent=1))
        return 1 if total else (2 if a.sin_render else 0)

    print("═" * 72)
    if a.sin_render:
        print("INCOMPLETO · %d fallos en %d piezas, y SIN las dos comprobaciones de"
              % (total, len(slugs)))
        print("montaje (desbordamiento y sin-JS). Esto no es un verde. Sale con 2.")
        return 2
    if total:
        print("ROJO · %d fallos en %d piezas. No se publica." % (total, len(slugs)))
        return 1
    print("VERDE · %d piezas, 0 fallos, y el control positivo saltó en esta misma"
          % len(slugs))
    print("ejecución. Se puede publicar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
