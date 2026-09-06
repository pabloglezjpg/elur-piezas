# -*- coding: utf-8 -*-
"""Extractor de regiones de HTML que respeta el anidamiento.

POR QUÉ EXISTE, Y ES UNA LECCIÓN CARA
La primera versión de la comprobación «texto contra gráfico» delimitaba los
gráficos con expresiones regulares. Dio doce hallazgos sobre piezas correctas.
Corregida, dio tres. Los quince eran del extractor, ninguno de las piezas:

  · «146» se declaraba en el gráfico y estaba en el gráfico, en
    `<div class="cmp-value">+146%</div>` — pero dentro de `<div class="cmp-row">`,
    y un `.*?</div>` cierra en el primer `</div>`, que es el del hermano anterior.
  · «2.071» se declaraba en el cuerpo y estaba en el cuerpo, en un
    `<p class="dash-note">` que vive DENTRO del bloque del gráfico. Por
    nombre de etiqueta era gráfico; por contenido es prosa.

No se puede delimitar HTML anidado con una expresión regular. Esto usa
html.parser, que es de la biblioteca estándar y sí lleva la cuenta.

La norma del repo aplicada a uno mismo: un detector que salta con todo es tan
inútil como uno que no salta nunca (CLAUDE.md:125).
"""
from html.parser import HTMLParser
import html as _html
import re

VACIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
          "meta", "param", "source", "track", "wbr"}


class _Recorte(HTMLParser):
    """Devuelve el HTML interno de cada elemento que cumpla `predicado`.

    Las regiones anidadas no se cuentan dos veces: si una figura contiene otra,
    solo se abre la de fuera. Es lo que hace que el texto de un gráfico se
    cuente una vez y no tantas como divs tenga dentro.
    """

    def __init__(self, predicado):
        super().__init__(convert_charrefs=False)
        self.predicado = predicado
        self.regiones = []
        self._pila = []          # etiquetas abiertas
        self._captura = None     # [profundidad_de_apertura, trozos]

    def handle_starttag(self, tag, attrs):
        crudo = self.get_starttag_text() or ""
        if self._captura is not None:
            self._captura[1].append(crudo)
            if tag not in VACIOS:
                self._pila.append(tag)
            return
        if tag not in VACIOS:
            self._pila.append(tag)
        if self.predicado(tag, dict(attrs)):
            # La profundidad de cierre es la de ANTES de abrir este elemento.
            self._captura = [len(self._pila) - (0 if tag in VACIOS else 1), []]

    def handle_endtag(self, tag):
        if self._pila and self._pila[-1] == tag:
            self._pila.pop()
        elif tag in self._pila:                 # cierre desemparejado
            while self._pila and self._pila.pop() != tag:
                pass
        if self._captura is not None:
            if len(self._pila) <= self._captura[0]:
                self.regiones.append("".join(self._captura[1]))
                self._captura = None
            else:
                self._captura[1].append("</%s>" % tag)

    def handle_startendtag(self, tag, attrs):
        crudo = self.get_starttag_text() or ""
        if self._captura is not None:
            self._captura[1].append(crudo)
        elif self.predicado(tag, dict(attrs)):
            self.regiones.append(crudo)

    def handle_data(self, d):
        if self._captura is not None:
            self._captura[1].append(d)

    def handle_entityref(self, name):
        if self._captura is not None:
            self._captura[1].append("&%s;" % name)

    def handle_charref(self, name):
        if self._captura is not None:
            self._captura[1].append("&#%s;" % name)


def regiones(doc, predicado):
    """HTML interno de cada elemento que cumpla predicado(tag, attrs)."""
    p = _Recorte(predicado)
    try:
        p.feed(doc)
        p.close()
    except Exception:
        pass                     # documento malformado: se devuelve lo hallado
    return p.regiones


def por_clase(*clases):
    """Predicado: la etiqueta es una de `clases` o lleva una de esas clases."""
    quiere = set(clases)

    def pred(tag, attrs):
        if tag in quiere:
            return True
        cls = (attrs.get("class") or "").split()
        return any(c in quiere for c in cls)
    return pred


def sin_marcas(x):
    """Texto plano, entidades resueltas y espacios normalizados."""
    x = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", x, flags=re.S | re.I)
    x = re.sub(r"<[^>]+>", " ", x)
    x = _html.unescape(x)
    x = x.replace(" ", " ").replace(" ", " ").replace(" ", " ")
    return " ".join(x.split())
