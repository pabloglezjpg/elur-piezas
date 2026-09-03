#!/usr/bin/env python3
"""
Verificador de páginas traducidas al inglés — piezas.elur.es

Existe porque el verificador anterior solo miraba NODOS DE TEXTO VISIBLE, y por
eso dejó pasar, en tres tandas distintas:
  1. los nodos que solo contienen números (etiquetas de SVG, celdas de tabla),
  2. el formato numérico impuesto por código en assets/formato.js,
  3. el contenido de los atributos <meta> y el texto incrustado en el JPG social.

Este barre TAMBIÉN:
  · content de toda etiqueta <meta>
  · todo atributo alt, title y aria-label
  · <desc> y <title> dentro de los SVG
  · TODO el JSON-LD (schema.org): headline, description, keywords, articleSection,
    inLanguage, image y mainEntityOfPage.@id
  · coherencia og:url == canonical
  · que og:image / twitter:image apunten a un recurso -en

Uso:  python3 herramientas/verificar_en.py <slug> [...]
      python3 herramientas/verificar_en.py --autotest    (control positivo)
"""
import re, sys, os, json

# coma decimal ESPAÑOLA: coma + 1-2 dígitos, o 4+; nunca exactamente 3 (millar inglés)
RE_COMA_DEC = re.compile(r'\d,\d(?!\d\d(?!\d))\d*|\d,\d{1,2}(?!\d)')
# Un millar español nunca empieza por cero: «0.001» es un decimal inglés de tres
# cifras (una p de significación, por ejemplo), no «cero mil uno». La versión
# anterior lo marcaba como fallo y obligó a escribir «p < .001» para esquivarlo.
RE_PUNTO_MIL = re.compile(r'\b(?!0\.)\d{1,3}\.\d{3}(?!\d)')
# Un DOI es un identificador, no una cifra: «10.1016/j.tjnut.2025.05.004» lleva
# dentro «05.004» y disparaba el punto de millar en una pieza de ciencia, con la
# fuente escrita igual que en la página española. Se exime SOLO el token del DOI;
# el autotest comprueba que una coma decimal pegada a un DOI se sigue cazando.
RE_DOI = re.compile(r'\b10\.\d{4,9}/\S+')
PALABRAS_ES = ['millones','millón','dólares','años','año','empresa','mercado','cámara',
               'también','después','porque','según','ingresos','cifras','Fuentes','Análisis',
               'Lectura','Actualizada','Saltar','Economía','Gráfico','Momento','Portada',
               'pieza','valor','bolsa','acción','quería','comprar','pudo','sus','motivos',
               'desploma','cae','de la','se','los','las','una','por','con','para','está']
RE_ACENTO = re.compile(r'\b\w*[áéíóúñ¿¡]\w*\b')

# El castellano sin tildes era invisible. «28 de agosto de 2026» no lleva
# ninguna y pasaba las doce piezas: el control positivo lo destapó.
_MESES = ('enero|febrero|marzo|abril|mayo|junio|julio|agosto|'
          'septiembre|setiembre|octubre|noviembre|diciembre')
_MESES3 = 'ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic'
RE_FECHA_ES = re.compile(
    r'\b\d{1,2}\s+de\s+(?:%s)\b'          # 28 de agosto
    r'|\b(?:%s)\s+de\s+\d{4}\b'            # agosto de 2026
    r'|\b\d{1,2}-(?:%s)-\d{2,4}\b'          # 18-ago-2026
    % (_MESES, _MESES, _MESES3), re.I)

# Palabras funcionales castellanas que no llevan tilde y delatan texto sin
# traducir. Solo las que no son también inglesas ni nombres propios.
RE_PALABRA_ES = re.compile(
    r'\b(?:desde|hasta|entre|sobre|cuando|porque|aunque|mientras|'
    r'segun|durante|tambien|pero|sino|ademas|donde|quien|cuyo|'
    r'este|esta|estos|estas|ese|esa|esos|esas|aquel|'
    r'todos|todas|cada|otro|otra|otros|otras|mismo|misma|'
    r'anos|meses|semanas|dias|horas|veces|mil|millones|'
    r'segundo|tercero|cuarto|quinto)\b', re.I)

def campos(h):
    """Devuelve [(donde, texto)] de TODO lo traducible, no solo lo visible."""
    out = []
    for m in re.finditer(r'<meta\b[^>]*>', h, re.I):
        tag = m.group(0)
        key = (re.search(r'(?:name|property)="([^"]+)"', tag, re.I) or [None,''])[1]
        val = (re.search(r'content="([^"]*)"', tag, re.I) or [None,''])[1]
        if val and re.search(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]', val) and not key.lower().startswith(
                ('viewport','charset','http-equiv','theme-color','color-scheme')):
            out.append((f'meta[{key}]', val))
    for attr in ('alt', 'title', 'aria-label'):
        for m in re.finditer(rf'\b{attr}="([^"]*)"', h, re.I):
            v = m.group(1)
            if v and re.search(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]', v):
                out.append((f'@{attr}', v))
    for tag in ('desc', 'title'):
        for m in re.finditer(rf'<{tag}[^>]*>(.*?)</{tag}>', h, re.S | re.I):
            v = re.sub(r'\s+', ' ', m.group(1)).strip()
            if v: out.append((f'<{tag}>', v))
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, re.S | re.I):
        try: datos = json.loads(m.group(1))
        except Exception: out.append(('ld+json', 'BLOQUE QUE NO PARSEA')); continue
        def anda(o, pref=''):
            if isinstance(o, dict):
                for k, v in o.items(): anda(v, f'{pref}.{k}')
            elif isinstance(o, list):
                for i, v in enumerate(o): anda(v, f'{pref}[{i}]')
            elif isinstance(o, str) and re.search(r'[A-Za-zÁÉÍÓÚÑáéíóúñ]', o):
                out.append((f'ld+json{pref}', o))
        anda(datos)
    cuerpo = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', h, flags=re.S)
    # Excepción legítima: lo marcado con lang="es" es castellano A PROPÓSITO —
    # el enlace «Versión en español» debe ir en su idioma de destino, y así lo
    # anuncian correctamente los lectores de pantalla. Se excluye del barrido,
    # pero SOLO si lleva el lang; castellano sin marcar sigue siendo un fallo.
    # Cualquier idioma MARCADO explícitamente y distinto del inglés es deliberado:
    # el enlace «Versión en español», una cita literal en francés dentro de un pie.
    # Se exime del barrido. Sin marcar sigue siendo un fallo.
    cuerpo = re.sub(r'<(\w+)[^>]*\blang="(?!en)[a-z-]+"[^>]*>.*?</\1>', ' ', cuerpo, flags=re.S | re.I)
    vis = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', cuerpo))
    out.append(('texto visible', vis))
    return out


# ── AÑADIDO 2-sep-2026 ────────────────────────────────────────────────────────
# Tres cosas que el verificador no miraba y que son justo por donde se cuela el
# error: que la cifra inglesa sea la MISMA que la declarada en el datos.json de
# la pieza española, que el JPG social exista DE VERDAD (no basta un 200: un
# JPG que devuelve HTML no existe), y el recorrido de las doce de una vez.

def a_ingles(v):
    """1.093,5 → 1,093.5 · 211,4 → 211.4 · 276.300 → 276,300"""
    if not re.fullmatch(r'[+−-]?[\d.,]+%?', v or ''):
        return None                       # no es una cifra: «Superávit», fechas…
    return v.replace('.', '\x00').replace(',', '.').replace('\x00', ',')


def cifras_manifiesto(slug, h):
    """Cada cifra del datos.json español tiene que estar, en inglés, en la
    página inglesa. Si falta o aparece con la puntuación española, es fallo."""
    fallos = []
    man = f"{slug}/datos.json"
    if not os.path.exists(man):
        return [('datos.json', 'la pieza española no tiene manifiesto: no se puede cotejar')]
    d = json.load(open(man, encoding='utf-8'))
    plano = ' '.join(txt for _, txt in campos(h))
    for clave, e in d.get('cifras', {}).items():
        if e.get('retirado') or e.get('solo_es'):
            continue
        es = str(e.get('valor', ''))
        en = a_ingles(es)
        if en is None:
            continue
        borde = r'(?<![\d.,])%s(?![\d])(?![.,]\d)'
        if re.search(borde % re.escape(es), plano) and es != en:
            fallos.append((f'cifra {clave}', f'sigue con puntuación española: «{es}»'))
        elif not re.search(borde % re.escape(en), plano):
            fallos.append((f'cifra {clave}', f'«{en}» no aparece en la página inglesa (el español declara «{es}»)'))
    return fallos


def imagen_social(slug, h):
    """Que el portada-en.jpg exista, sea un JPEG de verdad y no un HTML."""
    fallos = []
    m = re.search(r'property="og:image"[^>]*content="([^"]+)"', h)
    if not m:
        return [('og:image', 'no hay og:image')]
    url = m.group(1)
    nombre = url.rsplit('/', 1)[-1]
    # Que exista no basta: «portada.jpg» también existe. El control positivo
    # metió la portada española en og:image y solo saltó de rebote, por el
    # JSON-LD — y casio-encogerse no tiene esa clave, así que se coló.
    if '-en' not in nombre:
        fallos.append(('og:image', f'apunta a la portada española: {nombre}'))
    ruta = os.path.join(slug, nombre)
    if not os.path.exists(ruta):
        return [('og:image', f'el fichero no existe: {ruta}')]
    with open(ruta, 'rb') as f:
        cab = f.read(3)
    tam = os.path.getsize(ruta)
    if cab != b'\xff\xd8\xff':
        fallos.append(('og:image', f'{ruta} no es un JPEG: empieza por {cab!r}'))
    if tam < 8000:
        fallos.append(('og:image', f'{ruta} pesa {tam} bytes: demasiado poco para una portada'))
    return fallos


def revisar(path):
    h = open(path, encoding='utf-8').read()
    fallos = []
    # CONTROL POSITIVO: si no leemos nada reconocible, el escáner no vale
    if len(h) < 500 or '<html' not in h.lower():
        return [('FATAL', 'ESCÁNER CIEGO: el fichero no se ha leído')], 0
    revisados = 0
    for donde, txt in campos(h):
        revisados += 1
        for w in PALABRAS_ES:
            if re.search(r'(?<![A-Za-zÁÉÍÓÚÑáéíóúñ])' + re.escape(w) + r'(?![A-Za-zÁÉÍÓÚÑáéíóúñ])', txt):
                fallos.append((donde, f'castellano «{w}» → {txt[:90]}')); break
        else:
            # Palabras inglesas que llevan tilde de origen. Sin esta lista, el
            # verificador marca «cliché» o «café» como castellano — y «café»
            # aparece en cada párrafo de la pieza del café.
            t2 = txt.replace('González','').replace('Pablo','').replace('Añ','')
            for w in ('cliché','clichés','café','cafés','naïve','résumé','fiancé',
                      'façade','décor','début','exposé','protégé','doppelgänger'):
                t2 = re.sub(w, '', t2, flags=re.I)
            acc = RE_ACENTO.findall(t2)
            if acc: fallos.append((donde, f'acento español {acc[:3]} → {txt[:80]}'))
        f = RE_FECHA_ES.findall(txt)
        if RE_FECHA_ES.search(txt):
            fallos.append((donde, f'fecha en formato español → {txt[:80]}'))
        pal = RE_PALABRA_ES.findall(txt)
        if pal:
            fallos.append((donde, f'palabra castellana sin tilde {pal[:4]} → {txt[:80]}'))
        num = RE_DOI.sub(' ', txt)   # los DOI quedan fuera del barrido numérico
        if RE_COMA_DEC.search(num):
            fallos.append((donde, f'coma decimal española {RE_COMA_DEC.findall(num)[:4]} → {txt[:80]}'))
        if RE_PUNTO_MIL.search(num):
            fallos.append((donde, f'punto de millar español {RE_PUNTO_MIL.findall(num)[:4]} → {txt[:80]}'))
    # coherencia og:url == canonical
    can = (re.search(r'rel="canonical"[^>]*href="([^"]+)"', h) or [None,''])[1]
    ogu = (re.search(r'property="og:url"[^>]*content="([^"]+)"', h) or
           re.search(r'content="([^"]+)"[^>]*property="og:url"', h) or [None,''])[1]
    if can and ogu and can.rstrip('/') != ogu.rstrip('/'):
        fallos.append(('og:url≠canonical', f'canonical={can}  og:url={ogu}'))
    if can and '/en/' not in can: fallos.append(('canonical', f'no apunta a /en/: {can}'))
    if ogu and '/en/' not in ogu: fallos.append(('og:url', f'no apunta a /en/: {ogu}'))
    # imagen social en inglés
    for prop in ('og:image', 'og:image:secure_url', 'twitter:image'):
        m = re.search(rf'(?:property|name)="{re.escape(prop)}"[^>]*content="([^"]+)"', h)
        if m and '-en' not in m.group(1):
            fallos.append((prop, f'imagen no inglesa: {m.group(1)}'))
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', h, re.S | re.I):
        try: d = json.loads(m.group(1))
        except Exception: continue
        idp = (d.get('mainEntityOfPage') or {}).get('@id', '') if isinstance(d.get('mainEntityOfPage'), dict) else ''
        if idp and '/en/' not in idp:
            fallos.append(('ld+json @id', f'apunta a la página española: {idp}'))
        il = d.get('inLanguage', '')
        if il and not str(il).lower().startswith('en'):
            fallos.append(('ld+json inLanguage', f'declara «{il}», no «en»'))
        img = d.get('image')
        img = img[0] if isinstance(img, list) and img else img
        if isinstance(img, str) and '-en' not in img:
            fallos.append(('ld+json image', f'imagen no inglesa: {img}'))
    if re.search(r'<html[^>]*lang="(?!en)', h): fallos.append(('lang', 'el html no declara lang="en"'))
    # Las dos comprobaciones que necesitan ficheros del repo solo se hacen sobre
    # rutas reales «<slug>/en/index.html». Los ficheros sintéticos del control
    # positivo no tienen manifiesto ni portada, y disparaban un falso fallo.
    if re.fullmatch(r'[^/]+/en/index\.html', path.replace(os.sep, '/')):
        slug = path.replace(os.sep, '/').split('/')[0]
        fallos += cifras_manifiesto(slug, h)
        fallos += imagen_social(slug, h)
    return fallos, revisados

def autotest():
    """Control positivo: inyecta castellano en un atributo meta y en un alt."""
    print("═══ CONTROL POSITIVO DEL VERIFICADOR ═══")
    base = ('<html lang="en"><head>'
            '<link rel="canonical" href="https://x.es/s/en/">'
            '<meta property="og:url" content="https://x.es/s/en/">'
            '<meta property="og:image" content="/s/portada-en.jpg">'
            '<meta name="description" content="A clean english description">'
            '</head><body><img alt="A chart in english"><p>All fine here</p>'
            + 'x'*500 + '</body></html>')
    LD = ('<script type="application/ld+json">{"@type":"Article",'
          '"headline":"A clean headline","inLanguage":"en",'
          '"image":["https://x.es/s/portada-en.jpg"],'
          '"mainEntityOfPage":{"@id":"https://x.es/s/en/"}}</script>')
    pruebas = [
        ("limpio", base, 0),
        ("castellano en meta", base.replace('A clean english description','Portada de la pieza'), 1),
        ("castellano en alt", base.replace('A chart in english','La caída de GoPro'), 1),
        ("coma decimal en meta", base.replace('A clean english description','Down 99,4 percent'), 1),
        ("og:url español", base.replace('content="https://x.es/s/en/"','content="https://x.es/s/"'), 1),
        ("imagen española", base.replace('portada-en.jpg','portada.jpg'), 1),
        ("ld+json @id español", base.replace('</head>', LD.replace('/s/en/"}','/s/"}') + '</head>'), 1),
        ("ld+json inLanguage es", base.replace('</head>', LD.replace('"en"','"es"') + '</head>'), 1),
        ("ld+json castellano", base.replace('</head>', LD.replace('A clean headline','La caída de GoPro') + '</head>'), 1),
        ("ld+json limpio", base.replace('</head>', LD + '</head>'), 0),
        ("enlace de idioma marcado", base.replace('<p>All fine here</p>',
            '<p><a href="../" lang="es">Versión en español</a></p>'), 0),
        ("castellano SIN marcar", base.replace('<p>All fine here</p>',
            '<p><a href="../">Versión en español</a></p>'), 1),
        ("DOI no es una cifra", base.replace('A clean english description',
            'See doi 10.1016/j.tjnut.2025.05.004'), 0),
        ("coma decimal PEGADA a un DOI", base.replace('A clean english description',
            'doi 10.1016/j.tjnut.2025.05.004 and 3,5 cups'), 1),
    ]
    ok = True
    for nombre, html, esperado in pruebas:
        open('/tmp/_vt.html','w',encoding='utf-8').write(html)
        f,_ = revisar('/tmp/_vt.html')
        caza = len(f) > 0
        bien = caza == bool(esperado)
        ok &= bien
        print(f"  {'✅' if bien else '✗✗ FALLA'} {nombre:24} → {'detecta' if caza else 'no detecta'}"
              + (f"  [{f[0][0]}]" if f else ""))
    os.path.exists('/tmp/_vt.html') and os.remove('/tmp/_vt.html')
    ok &= autotest_cifras_e_imagen()
    print("  RESULTADO:", "el verificador funciona ✅" if ok else "EL VERIFICADOR NO VALE ✗✗")
    return ok


def autotest_cifras_e_imagen():
    """Control positivo de las comprobaciones añadidas el 2-sep-2026: cifra
    desviada del manifiesto, coma decimal en una etiqueta de SVG y JPG social
    que no existe. Se hace sobre una copia en /tmp: no toca el repo."""
    import shutil, tempfile
    ref = 'caida-gopro'
    if not os.path.exists(f'{ref}/en/index.html'):
        print('  (sin pieza de referencia, no se puede probar)'); return True
    base = open(f'{ref}/en/index.html', encoding='utf-8').read()
    tmp = tempfile.mkdtemp()
    os.makedirs(f'{tmp}/{ref}/en', exist_ok=True)
    for f in ('datos.json', 'portada-en.jpg'):
        if os.path.exists(f'{ref}/{f}'): shutil.copy(f'{ref}/{f}', f'{tmp}/{ref}/{f}')
    casos = [
        ('cifra desviada del manifiesto', lambda h: h.replace('98.47', '98.48'), True),
        ('coma decimal en etiqueta SVG',
         lambda h: re.sub(r'(<text[^>]*>)(\d+)\.(\d)', r'\g<1>\g<2>,\g<3>', h, count=1), True),
        ('og:image inexistente', lambda h: h.replace('portada-en.jpg', 'portada-no.jpg'), True),
        ('página intacta', lambda h: h, False),
    ]
    cwd = os.getcwd(); ok = True
    try:
        os.chdir(tmp)
        for nombre, muta, esperado in casos:
            open(f'{ref}/en/index.html', 'w', encoding='utf-8').write(muta(base))
            f, _ = revisar(f'{ref}/en/index.html')
            bien = bool(f) == esperado
            ok &= bien
            print(f"  {'✅' if bien else '✗✗ FALLA'} {nombre:26} → "
                  f"{'detecta' if f else 'no detecta'}" + (f"  [{f[0][0]}]" if f else ""))
    finally:
        os.chdir(cwd); shutil.rmtree(tmp, ignore_errors=True)
    return ok

if __name__ == '__main__':
    if '--autotest' in sys.argv:
        sys.exit(0 if autotest() else 1)
    total = 0
    slugs = sys.argv[1:]
    if not slugs:
        slugs = sorted(d.split('/')[0] for d in
                       __import__('glob').glob('*/index.html')
                       if d.split('/')[0] not in ('gracias', 'en'))
        # El índice inglés es una superficie publicada más y no lo miraba nadie:
        # vive en «en/index.html», no en «<slug>/en/index.html».
        if os.path.exists('en/index.html'):
            slugs.append('.')
    for slug in slugs:
        p = 'en/index.html' if slug == '.' else f"{slug}/en/index.html"
        print(f"\n═══ {p}")
        if not os.path.exists(p): print("  NO EXISTE"); total += 1; continue
        fallos, n = revisar(p)
        print(f"  campos revisados: {n}")
        for donde, msg in fallos: print(f"  ✗ [{donde}] {msg}")
        print(f"  → {len(fallos)} fallo(s)" if fallos else "  → LIMPIA ✅")
        total += len(fallos)
    sys.exit(1 if total else 0)
