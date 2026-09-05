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


OPUESTO = {"negativo": ("+",), "positivo": ("\u2212", "-")}

# Una fecha, en cualquiera de las formas que usa el sitio en los dos idiomas.
RE_FECHA = re.compile(
    r"\b(20\d\d"
    r"|ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic"
    r"|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
    r"|jan|apr|aug|dec|january|february|march|april|june|july|august|september|october|november|december"
    r"|[1-4][TQ]\b|trimestre|quarter|ejercicio|financial year)\b", re.I)


RE_AHORA = re.compile(
    r"\b(hoy|actualmente|ahora mismo|a d[íi]a de hoy|en la actualidad"
    r"|today|currently|right now|as of today)\b", re.I)


def _frase(texto, i, j, tope=420):
    """La frase que contiene texto[i:j], acotada a `tope` por lado.

    Se mira la FRASE, no una ventana fija de caracteres: «comparando la
    instantánea del 31 de mayo de 2026 con la tienda en vivo: iMac …, MacBook …,
    Mac Studio … (+25,0%)» es una sola comparación fechada, y una ventana corta
    la partía por la mitad y la daba por indatada.
    """
    ini = max(0, i - tope)
    # Se incluye también la frase ANTERIOR: «…vale 333.000 M$ a finales de agosto
    # de 2026. Unas 6.660 veces lo que pedía» fecha la cifra igual de bien, y
    # exigir la fecha dentro de la misma frase obligaría a repetirla como un tic.
    corte = max(texto.rfind(". ", ini, i), texto.rfind("! ", ini, i), texto.rfind("? ", ini, i))
    if corte != -1:
        prev = max(texto.rfind(". ", ini, corte), texto.rfind("! ", ini, corte), texto.rfind("? ", ini, corte))
        ini = prev + 2 if prev != -1 else ini
    fin = min(len(texto), j + tope)
    m = re.search(r"[.!?]\s", texto[j:fin])
    return texto[ini: j + m.end() if m else fin]


def sin_fecha(valor, texto, ventana=None):
    # Un valor de una sola cifra («0», «2») casa en cualquier tabla y en
    # cualquier coordenada: no se puede localizar con fiabilidad, así que no se
    # le exige fecha. Se le exige a las que se pueden encontrar de verdad.
    if len(str(valor).strip()) < 2:
        return None
    """¿La cifra se publica aquí SIN una fecha cerca?

    La regla que dejó la auditoría del 4-9-2026, y es la más importante del
    proyecto: toda cifra que se mueva lleva su fecha pegada EN LA SUPERFICIE
    DONDE SE PUBLICA, no solo en el gráfico. «Ha perdido el 99,4%» caduca cada
    día; «el 99,4% que perdió hasta agosto de 2026» no caduca nunca.

    Solo se exige a las cifras declaradas DINAMICO: son las que el propio
    manifiesto reconoce que se mueven. Pedírselo a todas sería ruido.
    """
    for m in re.finditer(r"(?<![\d.,])%s(?![\d])(?![.,]\d)" % re.escape(valor), texto):
        ctx = _frase(texto, m.start(), m.end())
        # «hoy» no lo salva ninguna otra fecha de la frase. «Costaba 3.460 $ en
        # el 3T de 2025 y ronda HOY los 22.600» tiene fecha de inicio y un final
        # que caduca cada día: es justo el fallo que persigue esta regla.
        for a in RE_AHORA.finditer(ctx):
            # «Vale hoy · 25.08.2026» es correcto: el «hoy» lleva su fecha
            # pegada. «Ronda hoy los 22.600 dólares» no. Se mira el entorno
            # inmediato del adverbio, no el de la cifra.
            # La fecha que legitima un «hoy» va DETRÁS y pegada: «Vale hoy ·
            # 25.08.2026». Una fecha por delante pertenece al otro extremo de la
            # comparación —«costaba X en el 3T de 2025 y ronda hoy Y»— y no dice
            # cuándo es ese «hoy».
            if not RE_FECHA.search(ctx[a.end(): a.end() + 32]):
                return " ".join(ctx[:110].split())
        if not RE_FECHA.search(ctx):
            return " ".join(ctx[:110].split())
    return None


def signo_equivocado(valor, texto, signo):
    """¿Aparece el valor con el signo CONTRARIO al declarado?

    Una auditoría externa invirtió «\u221299,4%» a «+99,4%» en las cuatro
    superficies declaradas y este verificador siguió diciendo «0 fallos»: la
    frontera de `aparece()` excluye dígito, punto y coma, pero NO el signo, así
    que «99,4» casaba igual delante de un menos que de un más. En una pieza cuyo
    titular es una caída del 99%, ese es el error más caro que existe y era justo
    el que no se miraba.

    Sin signo declarado no se comprueba nada: «perdió el 99,4%» en prosa va sin
    signo y es correcto. Lo que se persigue es el signo INVERTIDO, no el ausente.
    """
    if not signo:
        return []
    malos = []
    plano = texto.replace(" ", "").replace("\u00a0", "")
    for s in OPUESTO.get(signo, ()):
        pat = re.escape(s) + r"\s?" + re.escape(valor) + r"(?![\d])(?![.,]\d)"
        if re.search(pat, texto) or re.search(pat.replace(r"\s?", ""), plano):
            malos.append(s + valor)
    return malos


# ── el barrido inverso ───────────────────────────────────────────────────────
# Todo lo de arriba comprueba LO DECLARADO. Eso deja el agujero de fondo: si
# declarar es opcional, un verde no significa nada — el verificador comprueba lo
# que le decimos que compruebe. El 5-9-2026 se midió: 394 cifras publicadas en las
# doce piezas, 56 declaradas; de las 277 que viven en dos o más superficies —el
# alcance que el propio manifiesto se atribuye—, 248 no estaban declaradas.
#
# Declararlas todas de golpe no es realista, así que esto funciona como trinquete:
# registra cuántas hay sin declarar por pieza y FALLA SI SUBEN. Lo que ya está,
# está; lo que se añada a partir de ahora, se declara.

RE_PUBLICADA = re.compile(
    r'(?<![\w.,/-])([+\u2212-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?|[+\u2212-]?\d+,\d+|[+\u2212-]?\d+)'
    r'\s*(%|\u20ac|\$|M\$|M\u20ac|M\u00a5|\u5104\u5186|millones|million|billion|bn|veces|times|\u00d7|puntos|pp|mg|nm|TB|GB)?')
RE_ANIO = re.compile(r'^(19|20)\d\d$')
RE_RUIDO = re.compile(r'DOI|10\.\d{4}|NCT\d|NDA\s?\d|viewBox|px|rgba?\(|#[0-9a-f]{3,6}', re.I)
DEUDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sin_declarar.json")


def publicadas(sup):
    """{valor: {superficies}} de todo lo que la pieza publica como cifra."""
    out = {}
    for nombre, txt in sup.items():
        if not txt:
            continue
        for m in RE_PUBLICADA.finditer(RE_RUIDO.sub(" ", txt)):
            val, uni = m.group(1), m.group(2)
            if not uni and RE_ANIO.match(val):
                continue                      # un año suelto no es un dato
            if not uni and "." not in val and "," not in val:
                continue                      # entero pelado sin unidad: demasiado ruido
            out.setdefault(val, set()).add(nombre)
    return out


def _misma_cifra(v):
    """«−99,4», «+99,4» y «99,4» son la misma cifra para saber si está declarada.

    El SIGNO sí se comprueba, pero en `signo_equivocado()`, que es su sitio. Aquí
    lo que se pregunta es otra cosa: si la cifra figura o no en el manifiesto.
    Sin esto, el barrido daba por no declaradas cinco que sí lo están —el −99,4
    de GoPro entre ellas— y engordaba la deuda con un fallo propio.
    """
    return re.sub(r"^[+\u2212-]", "", v).replace(".", "")


def sin_declarar(sup, man):
    """Cifras en DOS O MÁS superficies que el manifiesto no declara."""
    dec = {str(e.get("valor")) for e in man.get("cifras", {}).values()}
    dec |= {str(v) for e in man.get("cifras", {}).values() for v in e.get("variantes", [])}
    dec_n = {_misma_cifra(d) for d in dec}
    return sorted(v for v, s in publicadas(sup).items()
                  if len(s) >= 2 and v not in dec and _misma_cifra(v) not in dec_n)


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
        signo = e.get("signo")
        for nombre in e.get("superficies", []):
            if nombre not in sup:
                avisos.append(f"{clave}: superficie desconocida «{nombre}»")
                continue
            if not any(aparece(f, sup[nombre]) for f in formas):
                fallos.append(f"{clave}: «{valor}» NO aparece en «{nombre}»")
            for mal in signo_equivocado(valor, sup[nombre], signo):
                fallos.append(f"{clave}: declarada {signo} y en «{nombre}» aparece como «{mal}»")
            if e.get("tipo") == "DINAMICO":
                ctx = sin_fecha(valor, sup[nombre])
                if ctx:
                    fallos.append(f"{clave}: DINÁMICA y se publica sin fecha en «{nombre}» → …{ctx}…")
    return man, fallos, avisos, n, sin_declarar(sup, man)


def autotest(repo):
    """Control positivo: mete un error a propósito y exige que se cace."""
    print("CONTROL POSITIVO — se inyectan errores en memoria, no se toca ningún archivo\n")
    slugs = [d.split("/")[-2] for d in sorted(glob.glob(os.path.join(repo, "*/datos.json")))]
    if not slugs:
        print("  no hay ningún datos.json todavía"); return 1
    fallos_test = 0
    for slug in slugs:
        doc = open(os.path.join(repo, slug, "index.html"), encoding="utf-8").read()
        man, base, _, _, _ = revisa(slug, repo, doc)
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
        _, fallos, _, _, _ = revisa(slug, repo, roto)
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
                               if os.path.basename(os.path.dirname(d)) not in ("gracias", "en"))
    tot_f = tot_c = con_manifiesto = 0
    sin_manifiesto = []
    deuda = {}
    for slug in slugs:
        man, fallos, avisos, n, sin_dec = revisa(slug, repo)
        if man is None:
            sin_manifiesto.append(slug)
            continue
        con_manifiesto += 1
        tot_c += n
        tot_f += len(fallos)
        deuda[slug] = len(sin_dec)
        estado = "OK" if not fallos else f"{len(fallos)} FALLO(S)"
        print(f"\n{'='*72}\n{slug}  —  {n} cifras declaradas  —  {estado}")
        for f in fallos:
            print(f"  [FALLO] {f}")
        for w in avisos:
            print(f"  [aviso] {w}")

    print(f"\n{'='*72}")
    print(f"TOTAL: {tot_c} cifras en {con_manifiesto} piezas · {tot_f} fallos")

    # ── trinquete de cobertura del manifiesto ───────────────────────────────
    # Si declarar es opcional, un verde no significa nada. Esto no exige
    # declararlo todo de golpe —serían 248—, pero impide que la deuda crezca.
    previo = {}
    if os.path.exists(DEUDA):
        try:
            previo = json.load(open(DEUDA, encoding="utf-8"))
        except Exception as e:
            print(f"AVISO: no se ha podido leer {DEUDA} ({e}).")
    subidas = [(s, previo[s], deuda[s]) for s in deuda
               if s in previo and deuda[s] > previo[s]]
    nuevas = [s for s in deuda if s not in previo]
    total_deuda = sum(deuda.values())
    print(f"SIN DECLARAR: {total_deuda} cifras que se publican en dos o más "
          f"superficies y no están en su datos.json")
    if subidas:
        print("\nHan subido las cifras publicadas sin declarar:")
        for s, antes, ahora in sorted(subidas):
            print(f"  [FALLO] {s}: {antes} → {ahora}")
        print("Toda cifra nueva que viva en dos superficies va al manifiesto.")
        tot_f += len(subidas)
    elif not previo:
        print(f"Deuda registrada por primera vez en {DEUDA}.")
    if not subidas:
        # el suelo solo baja: si se declara una cifra, el listón se ajusta
        base = {k: min(v, previo[k]) if k in previo else v for k, v in deuda.items()}
        with open(DEUDA, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
    if sin_manifiesto:
        print(f"SIN MANIFIESTO ({len(sin_manifiesto)}): {', '.join(sin_manifiesto)}")
    if tot_f:
        print("Hay cifras que no dicen lo mismo en todas sus superficies. No publiques así.")
    # Una pieza publicada SIN manifiesto no es un aviso: es un hueco por el que
    # cabe cualquier cosa, y el verificador salía con 0 informando «43 cifras en
    # 11 piezas», que se lee como éxito. Si hay una pieza en el disco sin
    # datos.json, esto falla.
    if sin_manifiesto:
        print("Hay piezas publicadas sin datos.json: el verificador no las mira.")
        return 1
    return 1 if tot_f else 0


if __name__ == "__main__":
    sys.exit(main())
