# -*- coding: utf-8 -*-
"""Control positivo del verificador inglés, sobre los ficheros PUBLICADOS.

Existe porque `verificar_en.py --autotest` usa ficheros sintéticos, y un caso
sintético lo escribe quien ya sabe qué está buscando. Con las doce piezas dando
«limpia», este guion metió diez errores en cada una —sobre copias en /tmp, nunca
sobre el repo— y el verificador se escapó trece veces:

  · «28 de agosto de 2026» no lleva ni una tilde, así que un detector de
    castellano basado en acentos no ve una fecha española entera.
  · Una portada española en og:image solo saltaba de rebote, por el JSON-LD, y
    casio-encogerse no tiene esa clave.

Los dos agujeros están tapados. Este guion es la prueba de que siguen tapados.

Uso:  python3 herramientas/control_positivo.py
"""
import io, os, re, shutil, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slugs = sorted(d for d in os.listdir(REPO)
               if os.path.isfile(os.path.join(REPO, d, 'en', 'index.html')))

# Las tres inyecciones pedidas + tres más de las que ya han mordido en este repo.
def inyecciones(html, slug):
    I = []
    # 1. Cifra con formato español en texto visible
    m = re.search(r'>([^<>]*?)(\d{1,3}),(\d)([^<>]*?)<', html)
    if m: I.append(('cifra en formato español', html[:m.start()] +
                    m.group(0).replace(m.group(2)+','+m.group(3), m.group(2)+','+m.group(3)),
                    None))
    I.append(('cifra española inventada', html.replace('</h1>', ' 1.093,5</h1>', 1), 'h1'))
    # 2. Palabra en castellano olvidada
    I.append(('castellano olvidado', html.replace('</h1>', ' según el informe</h1>', 1), 'h1'))
    # 3. og:url apuntando a la página española
    I.append(('og:url a la versión española',
              re.sub(r'(<meta property="og:url" content="[^"]*?)en/"', r'\1"', html, count=1), 'og:url'))
    # 4. lang sin cambiar
    I.append(('lang="es" en la página inglesa', html.replace('<html lang="en">', '<html lang="es">', 1), 'lang'))
    # 5. Fecha en formato español
    I.append(('fecha en formato español', html.replace('</h1>', ' el 28 de agosto de 2026</h1>', 1), 'fecha'))
    # 6. portada española en og:image
    I.append(('og:image a la portada española', html.replace('portada-en.jpg', 'portada.jpg'), 'og:image'))
    # 7-9. Puntuación: comilla recta, apóstrofo recto y guillemet, en texto visible
    I.append(('comilla recta en el cuerpo', html.replace('</h1>', ' the \"thing\"</h1>', 1), 'recta'))
    I.append(('apóstrofo recto en el cuerpo', html.replace('</h1>', ' it\'s here</h1>', 1), 'apostrofo'))
    I.append(('guillemet en el cuerpo', html.replace('</h1>', ' «quoted»</h1>', 1), 'guillemet'))
    # 10. Y en un metadato, que es donde el proyecto siempre falla
    I.append(('apóstrofo recto en la meta description',
              html.replace('<meta name="description" content="', '<meta name="description" content="It\'s ', 1), 'meta'))
    return [(n, h) for n, h, _ in I[1:]]

fallos_del_control = []
total = 0
for slug in slugs:
    src = os.path.join(REPO, slug, 'en', 'index.html')
    html = io.open(src, encoding='utf-8').read()
    for nombre, roto in inyecciones(html, slug):
        total += 1
        tmp = tempfile.mkdtemp()
        try:
            # copia mínima: la pieza entera + herramientas + assets
            for d in (slug, 'herramientas', 'assets'):
                shutil.copytree(os.path.join(REPO, d), os.path.join(tmp, d))
            io.open(os.path.join(tmp, slug, 'en', 'index.html'), 'w', encoding='utf-8').write(roto)
            p = subprocess.run([sys.executable, 'herramientas/verificar_en.py', slug],
                               cwd=tmp, capture_output=True, text=True)
            if p.returncode == 0:
                fallos_del_control.append(f'{slug}: NO caza «{nombre}»')
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

print(f'inyecciones probadas: {total}  ({len(slugs)} piezas × 10)')
if fallos_del_control:
    print(f'\n✗ EL VERIFICADOR SE ESCAPA {len(fallos_del_control)} VECES:')
    for f in fallos_del_control: print('   ', f)
    sys.exit(1)
print('\n✅ el verificador caza las 10 inyecciones en todas las piezas')
