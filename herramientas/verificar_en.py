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
RE_PUNTO_MIL = re.compile(r'\b\d{1,3}\.\d{3}(?!\d)')
PALABRAS_ES = ['millones','millón','dólares','años','año','empresa','mercado','cámara',
               'también','después','porque','según','ingresos','cifras','Fuentes','Análisis',
               'Lectura','Actualizada','Saltar','Economía','Gráfico','Momento','Portada',
               'pieza','valor','bolsa','acción','quería','comprar','pudo','sus','motivos',
               'desploma','cae','de la','se','los','las','una','por','con','para','está']
RE_ACENTO = re.compile(r'\b\w*[áéíóúñ¿¡]\w*\b')

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
    cuerpo = re.sub(r'<(\w+)[^>]*\blang="es"[^>]*>.*?</\1>', ' ', cuerpo, flags=re.S | re.I)
    vis = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', cuerpo))
    out.append(('texto visible', vis))
    return out

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
            t2 = txt.replace('González','').replace('Pablo','').replace('Añ','')
            acc = RE_ACENTO.findall(t2)
            if acc: fallos.append((donde, f'acento español {acc[:3]} → {txt[:80]}'))
        if RE_COMA_DEC.search(txt):
            fallos.append((donde, f'coma decimal española {RE_COMA_DEC.findall(txt)[:4]} → {txt[:80]}'))
        if RE_PUNTO_MIL.search(txt):
            fallos.append((donde, f'punto de millar español {RE_PUNTO_MIL.findall(txt)[:4]} → {txt[:80]}'))
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
    print("  RESULTADO:", "el verificador funciona ✅" if ok else "EL VERIFICADOR NO VALE ✗✗")
    return ok

if __name__ == '__main__':
    if '--autotest' in sys.argv:
        sys.exit(0 if autotest() else 1)
    total = 0
    for slug in sys.argv[1:]:
        p = f"{slug}/en/index.html"
        print(f"\n═══ {p}")
        if not os.path.exists(p): print("  NO EXISTE"); total += 1; continue
        fallos, n = revisar(p)
        print(f"  campos revisados: {n}")
        for donde, msg in fallos: print(f"  ✗ [{donde}] {msg}")
        print(f"  → {len(fallos)} fallo(s)" if fallos else "  → LIMPIA ✅")
        total += len(fallos)
    sys.exit(1 if total else 0)
