#!/usr/bin/env python3
"""Deriva de tarjeta: ¿afirma la portada algo que la pieza ya no afirma?

El fallo que motiva esto salió dos veces el 5 de septiembre de 2026, en la
misma tanda: se corrigió la tesis de `argentina-milei` en las diez superficies
de la pieza y las dos tarjetas de la portada siguieron diciendo «la pobreza
repunta» y «poverty stopped falling»; y `dijeron-que-no` siguió afirmando en
la portada «y se rió» después de que el cuerpo declarase esa risa en disputa.

Ningún verificador lo miraba porque no es una cifra: es prosa. Y la tarjeta es
la primera superficie que ve un editor cuando le pegan el enlace.

La prueba: cada trigrama de palabras con contenido de la tarjeta tiene que
existir en algún sitio de su pieza. Si la tarjeta dice algo que no está en
ninguna superficie de la pieza, o la tarjeta se quedó atrás o afirma de más.
"""
import html, json, os, re, sys, unicodedata

VACIAS = set("""el la los las un una unos unas de del al a ante bajo con contra desde
en entre hacia hasta para por segun sin sobre tras y e o u ni que se su sus lo le les
es son era eran fue ser esta estan este esta estos estas ya no mas muy como cuando
donde porque pero si tambien solo the of and to in on at for a an is are was were be
been it its this that these those with from by as has have had not but or if so than
then there their they them he she his her you your we our i""".split())

def normaliza(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9%.,]+", " ", t)

def contenido(t):
    # La puntuación pegada convertía «relato.» y «relato» en palabras distintas:
    # cinco de las dieciocho primeras alarmas eran eso y nada más.
    ps = (p.strip(".,") for p in normaliza(t).split())
    return [p for p in ps if p and p not in VACIAS and len(p) > 1]


def palabras(ps):
    """Palabras sueltas Y parejas consecutivas.

    Solo con palabras sueltas, «Blockbuster … y se rió» sobrevivía en la portada
    después de que la pieza declarase esa risa en disputa: su propio dek dice
    «Microsoft se rió del iPhone», así que «rió» existía. Lo que delata el fallo
    es la pareja —«millones rió» frente a «microsoft rió»—: el mismo verbo, otro
    sujeto. Con parejas el control positivo pasa de 3 de 4 a 4 de 4.
    """
    return set(ps) | {" ".join(ps[i:i + 2]) for i in range(len(ps) - 1)}


# Solo la prosa que AFIRMA algo. La etiqueta de sección, la cifra del badge,
# la fecha y los minutos de lectura son cromo: cruzarlos con el texto producía
# 276 falsos («18 ago. 2026 min», «economia empresa 13») y una prueba que grita
# 276 veces no es una prueba.
DESC = re.compile(r'<(?:p|span)[^>]*class="(?:home-card-desc|home-dek)"[^>]*>(.*?)</(?:p|span)>', re.S)

# Contra qué se compara. La primera versión usaba la pieza ENTERA y cazaba 1 de
# 3 en el control positivo: el cuerpo de `dijeron-que-no` dice «Microsoft se rió
# del iPhone», así que «rió» existía y la tarjeta podía seguir diciendo que
# Blockbuster se rió —lo que la pieza declara en disputa— sin que saltara nada.
# Una tarjeta no resume la pieza: resume su DEK. Ese es el suelo correcto.
RESUMEN = (r'<title>(.*?)</title>',
           r'<h1[^>]*>(.*?)</h1>',
           r'<p class="dek">(.*?)</p>',
           r'<meta name="description" content="([^"]*)"',
           r'<meta property="og:description" content="([^"]*)"',
           r'<meta name="twitter:description" content="([^"]*)"',
           r'"description":\s*"([^"]*)"')


def resumen(doc):
    return " ".join(" ".join(re.findall(pat, doc, re.S)) for pat in RESUMEN)


def tarjetas(portada, slug, href):
    """Sumario de la tarjeta de esa pieza en la portada (destacada o de rejilla)."""
    out = []
    for pat in (r'<a[^>]*class="home-feature[^"]*"[^>]*href="%s"[^>]*>(.*?)</a>',
                r'<a[^>]*href="%s"[^>]*>(.*?)</a>'):
        for bloque in re.findall(pat % re.escape(href), portada, re.S):
            out += DESC.findall(bloque)
    return out

def revisa(repo, slug):
    fallos = []
    for portada_p, pieza_p, href in (
            (f"{repo}/index.html", f"{repo}/{slug}/index.html", f"{slug}/"),
            (f"{repo}/en/index.html", f"{repo}/{slug}/en/index.html", f"../{slug}/en/")):
        if not (os.path.exists(portada_p) and os.path.exists(pieza_p)):
            continue
        portada = open(portada_p, encoding="utf-8").read()
        pieza = open(pieza_p, encoding="utf-8").read()
        suelo = palabras(contenido(resumen(pieza)))
        for bloque in tarjetas(portada, slug, href):
            for tri in sorted(palabras(contenido(bloque)) - suelo):
                fallos.append((os.path.relpath(portada_p, repo), tri))
    return fallos

# Quedan derivas que son sinónimos legítimos de la tarjeta —«cae» por «bajó»,
# «se disparan» por «se han multiplicado»—. Fallar por ellas sería un rojo
# permanente, y un rojo permanente se ignora. Trinquete: se guarda el conjunto
# de palabras aceptadas y solo falla una NUEVA.
#
# El suelo es el CONJUNTO, no la cuenta. Con la cuenta, meter «repunta» y quitar
# «sube», «52,9» y «baja» dejaba el número igual y el control positivo pasaba en
# falso: una sustitución es justo el fallo que esto persigue.
BASE = "herramientas/deriva_tarjeta.json"


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    completo = not sys.argv[1:]
    slugs = sys.argv[1:] or sorted(
        d for d in os.listdir(repo)
        if os.path.isdir(f"{repo}/{d}") and os.path.exists(f"{repo}/{d}/index.html")
        and d not in ("en", "herramientas", "assets"))
    ruta = f"{repo}/{BASE}"
    suelo = json.load(open(ruta, encoding="utf-8")) if os.path.exists(ruta) else {}
    total, nuevas, ahora = 0, [], {}
    for slug in slugs:
        f = revisa(repo, slug)
        total += len(f)
        vistas = sorted({f"{portada}|{w}" for portada, w in f})
        ahora[slug] = vistas
        aceptadas = set(suelo.get(slug, []))
        for v in vistas:
            if suelo.get(slug) is not None and v not in aceptadas:
                nuevas.append(f"{slug} [{v.split('|')[0]}]: «{v.split('|')[1]}»")
        estado = "OK" if not f else f"{len(f)} deriva(s)"
        print(f"{slug:24} {estado}")
        for portada, w in f:
            marca = " ← NUEVA" if suelo.get(slug) is not None and f"{portada}|{w}" not in aceptadas else ""
            print(f"    [{portada}] «{w}» no está en el resumen de la pieza{marca}")
    print(f"\nTOTAL: {total} derivas de tarjeta en {len(slugs)} piezas")
    if nuevas:
        print("\nLa tarjeta afirma algo que su pieza ya no afirma:")
        for x in nuevas:
            print("  [FALLO]", x)
        print("Si la pieza cambia de tesis, la portada cambia con ella.")
        return 1
    if completo:
        nuevo = {k: sorted(set(v) & set(suelo[k])) if k in suelo else v
                 for k, v in ahora.items()}
        if nuevo != suelo:
            json.dump(nuevo, open(ruta, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1, sort_keys=True)
            print(f"\nsuelo actualizado en {BASE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
