#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scaffold_pieza.py — el esqueleto de una pieza nueva, en un comando.

    python3 scaffold_pieza.py mi-pieza --titular "..." --dek "..." \
        --seccion "Economía · Empresa" --titular-en "..." --dek-en "..."
    python3 scaffold_pieza.py mi-pieza ... --aplicar        # escribe de verdad

Sin `--aplicar` no toca nada: enseña el diff y se calla. Es deliberado — este
guion escribe en cuatro sitios a la vez y uno de ellos es el sitemap.

QUÉ CREA
    <slug>/index.html          cabecera SEO completa: 28 metadatos
    <slug>/en/index.html       la misma, en inglés, con hreflang cruzado
    <slug>/datos.json          manifiesto vacío con su estructura

QUÉ DA DE ALTA
    index.html                 tarjeta de portada + ItemList + numberOfItems
    en/index.html              lo mismo, en inglés
    sitemap.xml                dos <url> con sus tres <xhtml:link>

POR QUÉ EXISTE
Una pieza publicada arrastra veintiocho metadatos por edición, y todos llevan
la URL escrita a mano. Copiarlos de otra pieza es veinte minutos y una lotería:
basta olvidar el `og:image:width` o dejar el canonical de la pieza de la que se
copió para que un editor pegue el enlace en Slack y le salga otra cosa. Nada de
eso es difícil; es que no duele hasta que ya está publicado.

NACE EN ROJO, Y ES A PROPÓSITO
Lo que genera lleva marcadores `[FALTA ...]` en todo hueco de contenido, así que
`verifica_pieza.py` lo rechaza hasta que se rellenan. Un esqueleto que naciera
en verde sería un esqueleto que se puede publicar vacío.
"""

import argparse
import io
import json
import os
import re
import sys
import unicodedata
from datetime import date

SITIO = "https://piezas.elur.es"
AUTOR = "Pablo González"

FALTA = "[FALTA %s]"


def slugifica(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def recorta(texto, tope):
    """Recorta a `tope` caracteres sin partir palabra."""
    t = " ".join(str(texto).split())
    if len(t) <= tope:
        return t
    corte = t[:tope].rsplit(" ", 1)[0]
    return corte.rstrip(" ,;:·—-") + "."


# ─────────────────────────────── plantillas ───────────────────────────────

CABECERA = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta name="author" content="{autor}">
<meta name="theme-color" content="#F4EFE4">

<!-- Open Graph -->
<meta property="og:type" content="article">
<meta property="og:locale" content="{locale}">
<meta property="og:site_name" content="{site_name}">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{imagen}">
<meta property="og:image:secure_url" content="{imagen}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{img_alt}">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_description}">
<meta name="twitter:image" content="{imagen}">
<meta name="twitter:image:alt" content="{img_alt}">

<link rel="preload" href="{raiz}assets/periodismo.css" as="style">
<link rel="stylesheet" href="{raiz}assets/periodismo.css">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": {headline_json},
  "description": {desc_json},
  "image": ["{imagen}"],
  "inLanguage": "{lang}",
  "articleSection": {seccion_json},
  "keywords": {keywords_json},
  "author": {{ "@type": "Person", "name": "{autor}" }},
  "publisher": {{ "@type": "Person", "name": "{autor}" }},
  "datePublished": "{fecha}",
  "dateModified": "{fecha}",
  "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{canonical}" }}
}}
</script>
  <link rel="alternate" hreflang="es" href="{SITIO}/{slug}/">
  <link rel="alternate" hreflang="en" href="{SITIO}/{slug}/en/">
  <link rel="alternate" hreflang="x-default" href="{SITIO}/{slug}/">

<style>
/* ============================================================
   {slug} — estilos propios de la pieza.
   Los tokens del sistema (--accent, --hairline, --paper-raised,
   --ink-70, --grey-warm, --terra) ya viven en periodismo.css.
   Aquí solo se declara lo que falte.

   NO copies aquí las reglas de .needs-js: viven en
   assets/interactives.css y se cargan con la librería. Copiarlas a
   mano es lo que hizo que seis piezas las llevaran repetidas y que
   una pieza nueva pudiera nacer sin ellas.
   ============================================================ */
#{id} {{
  --fs-body: 1rem;
  --fs-body-lg: 1.1rem;
  --lh-body: 1.62;
  --link: var(--terra);
  --link-hover: var(--accent-ink);
}}
</style>
</head>
<body>
<a class="skip-link" href="#{id}">{saltar}</a>

<header class="mast">
  <div class="wrap"><a class="mast-brand" href="{raiz}">PIEZAS</a></div>
</header>

<main id="{id}" class="pieza">
  <article class="wrap">

    <p class="kicker">{seccion}</p>
    <h1>{h1}</h1>
    <p class="dek">{dek}</p>
    <p class="byline">{autor} · <time datetime="{fecha}">{fecha_larga}</time> · <span class="lectura">{min_lectura}</span></p>

    <div class="body lead">
      <p>{cuerpo_1}</p>
    </div>

    <p class="nutgraf">{nutgraf}</p>

    <div class="body">
      <p>{cuerpo_2}</p>
    </div>

    <figure class="figure" id="fig-1">
      <p class="fig-head"><span class="fig-num">{grafico_num}</span> <span class="fig-title">{grafico_titulo}</span></p>
      <div class="fig-media">
        {grafico}
      </div>
      <p class="fig-note">{grafico_pie}</p>
      <p class="fig-source">{grafico_fuente}</p>
    </figure>

    <div class="body">
      <p>{cuerpo_3}</p>
    </div>

    <details class="sources">
      <summary>{fuentes_titulo}</summary>
      <ul>
        <li>{fuente_1}</li>
      </ul>
    </details>

  </article>
</main>

<footer class="foot"><div class="wrap"><p>{autor}</p></div></footer>

<script src="{raiz}assets/formato.js" defer></script>
<script src="{raiz}assets/graphics.js" defer></script>
<script src="{raiz}assets/interactives.js" defer></script>
</body>
</html>
"""

TARJETA = """      <li class="home-card reveal">
        <span class="home-num">{num:02d}</span>
        <a href="{href}">
          <span class="home-card-tag">{seccion}{cifra}</span>
          <span class="home-card-title">{titulo}</span>
          <span class="home-card-desc">{sumario}</span>
          <span class="home-card-meta">{fecha_corta} · {min_lectura}</span>
        </a>
      </li>
"""

ENTRADA_SITEMAP = """  <url>
    <loc>{loc}</loc>
    <lastmod>{fecha}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
    <xhtml:link rel="alternate" hreflang="es" href="{SITIO}/{slug}/"/>
    <xhtml:link rel="alternate" hreflang="en" href="{SITIO}/{slug}/en/"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{SITIO}/{slug}/"/>
  </url>
"""

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")
MESES_CORTO = ("ene.", "feb.", "mar.", "abr.", "may.", "jun.",
               "jul.", "ago.", "sept.", "oct.", "nov.", "dic.")
MESES_EN = ("January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December")


def construye_pagina(a, idioma):
    en = idioma == "en"
    d = date.fromisoformat(a.fecha)
    canonical = "%s/%s/%s" % (SITIO, a.slug, "en/" if en else "")
    imagen = "%s/%s/portada%s.jpg" % (SITIO, a.slug, "-en" if en else "")
    titular = a.titular_en if en else a.titular
    dek = a.dek_en if en else a.dek
    seccion = a.seccion_en if en else a.seccion
    desc = recorta(dek, 158)

    # Los marcadores del esqueleto inglés van EN INGLÉS. La primera versión
    # envolvía el texto castellano en «[MISSING ...]» y `verificar_en.py`
    # cazaba la pieza recién generada por tener prosa castellana en la edición
    # inglesa — con razón. El gate lo destapó en la primera prueba del andamio.
    HUECOS = {
        "og_alt":  ("alt de la portada social: qué se ve y qué cifra la sostiene",
                    "social image alt: what is shown and which figure holds it up"),
        "entrada": ("entradilla: el hecho, con su cifra y su fecha pegada",
                    "lede: the fact, with its figure and its date attached"),
        "nutgraf": ("nutgraf: por qué esto importa, en dos frases",
                    "nut graf: why this matters, in two sentences"),
        "cuerpo":  ("desarrollo", "body"),
        "cierre":  ("cierre: sin aforismo y sin «la pregunta útil no es X sino Y»",
                    "ending: no aphorism, no \u201cthe useful question is not X but Y\u201d"),
        "g_tit":   ("título del gráfico, SIN punto final",
                    "chart title, with NO full stop"),
        # Ojo: aquí NO se escribe el atributo literal que el gate prohíbe, o el
        # propio esqueleto lo publicaría y saltaría por su propio consejo.
        # Pasó en la primera prueba.
        "g_svg":   ("GRÁFICO: SVG con viewBox y el estado final ya dibujado en el "
                    "DOM. Colores en hex o por clase CSS, nunca con var() dentro "
                    "de un atributo de presentación: en Safari no se ve",
                    "CHART: SVG with a viewBox and the final state already drawn "
                    "in the DOM. Colours in hex or via a CSS class, never var() "
                    "inside a presentation attribute: Safari does not render it"),
        "g_pie":   ("pie: explicación oracional, con punto",
                    "caption: a full sentence, with a full stop"),
        "g_fte":   ("Fuente: quién genera el dato, no quién lo reproduce",
                    "Source: whoever generates the data, not whoever repeats it"),
        "fuente":  ("fuente primaria, con URL y fecha de consulta",
                    "primary source, with URL and date consulted"),
    }

    def f(clave):
        es_txt, en_txt = HUECOS[clave]
        return ("[MISSING %s]" % en_txt) if en else (FALTA % es_txt)

    return CABECERA.format(
        SITIO=SITIO, slug=a.slug, id=a.id, autor=AUTOR, fecha=a.fecha,
        lang="en" if en else "es",
        locale="en_GB" if en else "es_ES",
        site_name="Piezas · %s" % AUTOR,
        raiz="../../" if en else "../",
        canonical=canonical, imagen=imagen,
        title="%s | %s" % (titular, AUTOR),
        description=desc,
        og_title=recorta(titular, 70),
        og_description=recorta(dek, 200),
        img_alt=f("og_alt"),
        headline_json=json.dumps(titular, ensure_ascii=False),
        desc_json=json.dumps(dek, ensure_ascii=False),
        seccion_json=json.dumps(seccion, ensure_ascii=False),
        keywords_json=json.dumps(a.keywords, ensure_ascii=False),
        saltar="Skip to content" if en else "Saltar al contenido",
        seccion=seccion, h1=titular, dek=dek,
        fecha_larga=("%d %s %d" % (d.day, MESES_EN[d.month - 1], d.year) if en
                     else "%d de %s de %d" % (d.day, MESES[d.month - 1], d.year)),
        min_lectura="[min]" if en else "[min]",
        cuerpo_1=f("entrada"),
        nutgraf=f("nutgraf"),
        cuerpo_2=f("cuerpo"),
        cuerpo_3=f("cierre"),
        grafico_num="Chart 1" if en else "Gráfico 1",
        grafico_titulo=f("g_tit"),
        grafico=f("g_svg"),
        grafico_pie=f("g_pie"),
        grafico_fuente=f("g_fte"),
        fuentes_titulo="Sources and gaps" if en else "Fuentes y huecos declarados",
        fuente_1=f("fuente"),
    )


ESQUELETO_DATOS = {
    "pieza": None,
    "actualizado": None,
    "alcance": ("Manifiesto de datos. Declara las cifras que viven en más de una "
                "superficie —titular, dek, metadatos, gráficos, pies— que es donde "
                "este proyecto ha cometido todos sus errores. No cubre cada número "
                "del cuerpo. Lo comprueba herramientas/verificar_datos.py."),
    "cifras": {},
}

# La clave empieza por «_» a propósito: las herramientas del repo leen
# `cifras` y nada más, así que el ejemplo viaja como documentación y no como
# una cifra falsa. La primera versión metía el ejemplo DENTRO de `cifras` con
# valores «[FALTA ...]», y eso hacía fallar a `verificar_datos.py --autotest`
# sobre el repo entero: un esqueleto a medias rompía la báscula de todos.
# Un manifiesto vacío es válido; uno con cifras inventadas, no.
CIFRA_EJEMPLO = {
    "valor": "[FALTA valor tal y como se publica: 1.234,5]",
    "unidad": "[FALTA unidad]",
    "periodo": "[FALTA periodo: «ejercicio cerrado en marzo de 2026», nunca «FY26»]",
    "fuente": "[FALTA quién genera el dato]",
    "url": "[FALTA url de la fuente primaria]",
    "consultado": "[FALTA AAAA-MM-DD]",
    "tipo": "ESTABLE",
    "derivado": False,
    "superficies": ["cuerpo"],
}


# ─────────────────────────────── alta ───────────────────────────────

def alta_portada(doc, a, idioma):
    """Mete la tarjeta la primera y renumera; recoloca el ItemList."""
    en = idioma == "en"
    d = date.fromisoformat(a.fecha)
    href = "../%s/en/" % a.slug if en else "%s/" % a.slug
    tarjeta = TARJETA.format(
        num=1, href=href,
        seccion=a.seccion_en if en else a.seccion,
        cifra=('<b class="home-card-fig">%s</b>' % a.cifra) if a.cifra else "",
        titulo=a.titular_en if en else a.titular,
        sumario=recorta(a.dek_en if en else a.dek, 190),
        fecha_corta=("%d %s %d" % (d.day, MESES_EN[d.month - 1][:3], d.year) if en
                     else "%d %s %d" % (d.day, MESES_CORTO[d.month - 1], d.year)),
        min_lectura="[min]")

    m = re.search(r'(<ol class="home-list">\s*\n)', doc)
    if not m:
        raise SystemExit("no encuentro <ol class=\"home-list\"> en la portada %s" % idioma)
    doc = doc[:m.end()] + tarjeta + doc[m.end():]

    # Renumerar las tarjetas por orden de aparición.
    n = [0]

    def renum(mm):
        n[0] += 1
        return '<span class="home-num">%02d</span>' % n[0]
    doc = re.sub(r'<span class="home-num">\d+</span>', renum, doc)

    # ItemList: entrada nueva la primera, posiciones recorridas, y el contador.
    url = "%s/%s/%s" % (SITIO, a.slug, "en/" if en else "")
    nueva = ('        { "@type": "ListItem", "position": 1, "url": "%s", "name": %s },\n'
             % (url, json.dumps(a.titular_en if en else a.titular, ensure_ascii=False)))
    m = re.search(r'("itemListElement"\s*:\s*\[\s*\n)', doc)
    if not m:
        raise SystemExit("no encuentro itemListElement en la portada %s" % idioma)
    doc = doc[:m.end()] + nueva + doc[m.end():]
    pos = [0]

    def repos(mm):
        pos[0] += 1
        return '"position": %d' % pos[0]
    doc = re.sub(r'"position":\s*\d+', repos, doc)
    total = len(re.findall(r'"@type"\s*:\s*"ListItem"', doc))
    doc = re.sub(r'"numberOfItems"\s*:\s*\d+', '"numberOfItems": %d' % total, doc)
    return doc


def alta_sitemap(doc, a):
    bloques = ""
    for loc in ("%s/%s/" % (SITIO, a.slug), "%s/%s/en/" % (SITIO, a.slug)):
        bloques += ENTRADA_SITEMAP.format(loc=loc, fecha=a.fecha, SITIO=SITIO, slug=a.slug)
    i = doc.rfind("</urlset>")
    if i < 0:
        raise SystemExit("sitemap.xml sin </urlset>")
    return doc[:i] + bloques + doc[i:]


# ─────────────────────────────── principal ───────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--repo", default=os.path.expanduser("~/Desktop/elur-piezas"))
    ap.add_argument("--titular", default="[FALTA titular en castellano, SIN punto final]")
    ap.add_argument("--titular-en", default="[MISSING English headline, NO full stop]")
    ap.add_argument("--dek", default="[FALTA dek en castellano. Con punto si tiene dos frases.]")
    ap.add_argument("--dek-en", default="[MISSING English dek. With a full stop if it has two sentences.]")
    ap.add_argument("--seccion", default="[FALTA sección]")
    ap.add_argument("--seccion-en", default="[MISSING section]")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--cifra", default="", help="la cifra grande de la tarjeta de portada")
    ap.add_argument("--fecha", default=date.today().isoformat())
    ap.add_argument("--aplicar", action="store_true", help="escribe. Sin esto solo enseña el diff.")
    a = ap.parse_args()

    a.slug = slugifica(a.slug)
    a.id = re.sub(r"-.*$", "", a.slug) or a.slug
    repo = os.path.abspath(os.path.expanduser(a.repo))
    if not os.path.isdir(repo):
        raise SystemExit("no encuentro el repo en %s" % repo)
    destino = os.path.join(repo, a.slug)
    if os.path.exists(destino):
        raise SystemExit("«%s» ya existe. Este guion no pisa piezas." % a.slug)

    nuevos = {
        os.path.join(a.slug, "index.html"): construye_pagina(a, "es"),
        os.path.join(a.slug, "en", "index.html"): construye_pagina(a, "en"),
    }
    datos = dict(ESQUELETO_DATOS)
    datos["pieza"] = a.slug
    datos["actualizado"] = a.fecha
    datos["cifras"] = {}
    datos["_ejemplo_de_cifra"] = dict(CIFRA_EJEMPLO)
    nuevos[os.path.join(a.slug, "datos.json")] = json.dumps(datos, ensure_ascii=False, indent=2) + "\n"

    tocados = {}
    for nombre, idioma in (("index.html", "es"), (os.path.join("en", "index.html"), "en")):
        ruta = os.path.join(repo, nombre)
        with open(ruta, encoding="utf-8") as f:
            tocados[nombre] = alta_portada(f.read(), a, idioma)
    with open(os.path.join(repo, "sitemap.xml"), encoding="utf-8") as f:
        tocados["sitemap.xml"] = alta_sitemap(f.read(), a)

    if not a.aplicar:
        print("═" * 72)
        print("ENSAYO · no se ha escrito nada. Añade --aplicar para que escriba.")
        print("═" * 72)
        print("\nFICHEROS NUEVOS")
        for n, c in sorted(nuevos.items()):
            print("  + %-40s %5d bytes" % (n, len(c.encode("utf-8"))))
        print("\nFICHEROS MODIFICADOS")
        for n, c in sorted(tocados.items()):
            with open(os.path.join(repo, n), encoding="utf-8") as f:
                antes = f.read()
            print("  ~ %-40s %+6d bytes" % (n, len(c.encode()) - len(antes.encode())))
            import difflib
            d = list(difflib.unified_diff(antes.splitlines(), c.splitlines(),
                                          n, n, lineterm="", n=1))
            for l in d[:22]:
                print("      %s" % l)
            if len(d) > 22:
                print("      … %d líneas más" % (len(d) - 22))
        print("\nDESPUÉS DE --aplicar, EN ESTE ORDEN:")
        print("  1. rellena los [FALTA ...] — hasta entonces el gate te dirá que no")
        print("  2. python3 herramientas/hacer_portada.py %s" % a.slug)
        print("  3. python3 herramientas/tiempo_lectura.py --aplicar")
        print("  4. python3 verifica_pieza.py %s" % a.slug)
        return 0

    os.makedirs(os.path.join(destino, "en"))
    for nombre, contenido in nuevos.items():
        with io.open(os.path.join(repo, nombre), "w", encoding="utf-8") as f:
            f.write(contenido)
        print("  + %s" % nombre)
    for nombre, contenido in tocados.items():
        with io.open(os.path.join(repo, nombre), "w", encoding="utf-8") as f:
            f.write(contenido)
        print("  ~ %s" % nombre)
    print("\nHecho. Ahora rellena los [FALTA ...] y corre:")
    print("  python3 verifica_pieza.py %s" % a.slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
