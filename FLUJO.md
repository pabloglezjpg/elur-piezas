# Flujo · de la idea a publicada

> **Va en la raíz de `elur-piezas`.** Se ha escrito aquí porque este chat tiene
> denegada la escritura sobre ese repositorio.

Este fichero es **la única fuente de verdad del ciclo**. Si algo de aquí se
contradice con otro documento, manda este. Y si cambias el ciclo, cámbialo aquí
o el siguiente chat volverá a reconstruirlo desde cero.

`CLAUDE.md` cuenta **por qué** son las reglas. Esto cuenta **qué se hace**.

---

## 1 · El ciclo, y dónde está la puerta

| # | Paso | Skill | Con qué frase se dispara |
|---|---|---|---|
| 1 | Tema | `nueva-pieza-periodistica` | «tengo un tema», «¿esto da para pieza?», «quiero hacer una pieza sobre X» |
| 2 | Research | `limpiar-research-pieza` | «límpiame esto», «aquí está lo de Perplexity», «ordena el research» |
| 3 | Redacción | — | La escribe Pablo. **El texto tiene que sonar a él.** |
| 4 | Edición | `editar-pieza-periodistica` | «corrígeme esto», «te paso el borrador» — **o mandar capturas anotadas** |
| 5 | Verificación | `verificador-datos` | «verifica esto», «haz fact check». **Antes de escribir, no después** |
| 6 | Montaje | `montar-pieza-visual` | «la pieza está cerrada», «móntala», «pásala a diseño» |
| 7 | **CIERRE** | **`cerrar-pieza`** | **«ciérrala», «¿la publico?», «último repaso»** |
| 8 | Publicación | — | `SUBIR_PIEZAS.command`. **El push lo hace Pablo, siempre** |
| 9 | Después | `auditar-piezas-publicadas` | «audita las piezas», «¿sigue todo bien?», o vence algo del calendario |

**El paso 7 es una puerta, no una sugerencia.** `cerrar-pieza` da un veredicto de
una palabra —PUBLICA o NO PUBLICA— y exige tres cosas a la vez: el gate en
verde, cuatro lentes adversariales sin hallazgo de nivel A, y cuatro preguntas
contestadas por una persona. Si falta una, no se publica. No hay tercer estado.

Ese hueco entre el 6 y el 9 **no existía, y ese hueco fue un mes**: doce piezas
salieron en agosto y las tres auditorías llegaron después, con 97, 114 y 31
hallazgos sobre material ya publicado.

**Los tres momentos que se confunden, y cuál es cuál:**
`verificador-datos` pregunta *¿esto es cierto?* y va **antes de escribir**.
`cerrar-pieza` pregunta *¿cómo tumbo esto?* y va **antes de publicar**.
`auditar-piezas-publicadas` pregunta *¿ha dejado de ser cierto?* y va **después**.

> **Aviso de superficie.** En Claude Code el listado de skills está topado en
> 30.000 caracteres y las skills de cuenta pierden su descripción el 54% de las
> veces: puede que no se disparen solas. Las locales, en `~/.claude/skills/`, no
> la han perdido nunca. Si una skill de esta tabla no arranca sola, invócala por
> su nombre — existe.

---

## 2 · Las herramientas

**Pásales siempre `--repo`.** Su ruta por defecto no resuelve fuera de la sesión
que las escribió, y una herramienta que no encuentra el repo aborta limpiamente
—que es lo correcto— pero no hace nada.

### `herramientas/verifica_pieza.py` — el gate

```bash
python3 herramientas/verifica_pieza.py --repo . <slug>
python3 herramientas/verifica_pieza.py --repo . --todas
python3 herramientas/verifica_pieza.py --repo . --solo-control   # ¿funciona la báscula?
```

Antes de mirar nada, **rompe una copia a propósito** —una rotura por familia— y
exige que cada rotura suene. Si una no suena, se para y no evalúa. Un verde solo
significa algo si en esa misma ejecución se ha demostrado que el rojo era
posible.

Comprueba: desbordamiento a 375/768/1280 · que se lea sin JavaScript · SEO
completo en las dos ediciones · alta en sitemap y en las dos portadas · que lo
declarado en gráficos esté en un gráfico · coherencia de cifras entre ediciones
· `var()` en `fill=`/`stroke=` · `<svg>` sin `viewBox` · marcadores de plantilla
· cronología en orden · trinquete de retiradas declaradas. Y **llama a los
cuatro verificadores del repo**: solo da verde si todos dan verde.

| Salida | Qué significa | Qué haces |
|---|---|---|
| **0** | verde, y el control saltó en esta ejecución | sigues |
| **1** | **la pieza falla** | la arreglas |
| **2** | **la báscula está rota**: falta una herramienta o el control no saltó | la arreglas ANTES. Un 2 nunca es un verde |

### `herramientas/scaffold_pieza.py` — el esqueleto

```bash
python3 scaffold_pieza.py <slug> --repo . --titular "…" --dek "…" [--aplicar]
```

Crea las dos ediciones con los 28 metadatos puestos, `datos.json` vacío con su
estructura, y da de alta la pieza en `sitemap.xml`, en la portada y en la
inglesa, con el `ItemList` renumerado. Sin `--aplicar` solo enseña el diff.
**Nace en rojo a propósito**, por marcadores `[FALTA …]`: un esqueleto que
naciera en verde sería un esqueleto publicable vacío.

### `assets/interactives.js` — los interactivos

Se configuran por marcado, no escribiendo JS:

```
grupo      <div data-piezas-grupo="metrica"><button data-valor="paro">…
panel      <div data-piezas-panel="metrica" data-valor="paro">…
filtro     data-piezas-grupo + data-modo="atenua" + data-piezas-filtrable
selector   data-piezas-grupo + data-multiple           (varios a la vez)
quiz       <div data-piezas-quiz><div data-pregunta><button data-correcta>…
rango      <input type="range" data-piezas-rango="nombre">
cronómetro <span data-piezas-hito data-fecha="2026-03-06">
diferido   <button data-piezas-carga="../assets/three.min.js" data-destino="#x">
```

**Carga siempre `assets/interactives.css` con ella.** Y **no copies las reglas
de `.needs-js` en el `<style>` de la pieza**: viven ahí y solo ahí.

Lo que la librería no cubre —una escena 3D, un canvas— va en
`assets/<pieza>-escenas.js` y se engancha con `Piezas.componente()`, sin repetir
el armazón.

---

## 3 · Las trampas que ya han costado tiempo

**Un comprobador que no puede fallar no está comprobando.** El sitio devolvió
durante días **200 con la portada para cualquier ruta inexistente**. Cada
comprobación de «esta URL da 200» fue basura y todo daba verde. Por eso el gate
corre su control positivo **antes** de evaluar, y por eso el código 2 existe.

**`html,body{overflow-x:hidden}`** está en `periodismo.css:49`. Con eso,
`documentElement.scrollWidth === clientWidth` es **siempre** cierto en este
sitio: la medida global da verde por construcción. Lo que mide es la sonda por
elemento. Si alguna vez «no encuentra nada», sospecha de la sonda antes que de
la página.

**Los parches automáticos publicaron la fuente en vez del reemplazo.** El
extractor cogía la única cadena entrecomillada del «qué debería decir», y cuando
esa cadena era la fuente, publicaba la fuente. **Se lee el diff de cada
sustitución antes de dejarla escrita.** Nunca `--aplicar` a ciegas.

**`.git/index.lock` huérfano** ha bloqueado publicaciones en silencio. Primera
línea de cualquier comando de publicación: `rm -f .git/index.lock`.

**`datos.json` no es el censo de todo lo publicado.** Declara las cifras que
viven en más de una superficie: hoy **74 de 309**. Un «0 fallos» es verdad y
cubre una de cada cuatro. El trinquete de `sin_declarar.json` impide que la
deuda crezca; no la vacía.

**Lo mismo con las retiradas.** Hay **39 notas de corrección y 8 retiradas
declaradas**. `verificar_datos.py` vigila que una cifra marcada `retirado` no
siga viva en otra superficie —borrando antes la nota, para que la nota pueda
citar lo que retiró—, pero **solo vigila lo que se le declara**. Escribes una
corrección, declaras qué retira. No se puede sacar de la prosa: la nota contiene
a la vez lo retirado y lo corregido, y en `caida-gopro` el mismo «0,60» está
retirado como precio del 25 y es cierto como cierre del 24, en una frase.

**Una comilla recta es siempre un descuido**, y vive también en los metadatos.
Nunca la conviertas con un `sed` sobre el fichero: en los atributos HTML y en el
JSON-LD es obligatoria.

**Toda comprobación caduca.** Antes de afirmar un estado, vuelve a medirlo. Y en
un repositorio **se publica el commit, no el árbol de trabajo**.

---

## 4 · La regla que lo resume

> **Agentes donde hace falta criterio, herramienta donde hace falta cuenta.
> Modelo caro donde hace falta pensar, barato donde hace falta recoger.**

Y el corolario que este proyecto pagó caro: **script determinista donde no hace
falta ni pensar ni recoger, sino medir.** Medir un ancho no necesita un modelo
de ningún precio, y durante un mes se hizo con 53 fotos del móvil.

De ahí sale el eje entero: **el listón no sube escribiendo reglas más exigentes,
sube convirtiendo en código las que ya están escritas.** «Cero desbordamiento a
375, 768, 1024 y 1280» y «se lee entera sin JavaScript» llevaban escritas desde
el principio, eran correctas, y se incumplieron en diez piezas de doce. No
fallaron las reglas: falló que fueran prosa.

---

*Si este fichero deja de describir lo que se hace, arréglalo antes de seguir.*

---

## Código que entró sin revisión externa

**7 de septiembre de 2026, commit `5db935f`.** Entraron 2.632 líneas en una sola subida,
instaladas por el asistente de Pablo. De ellas, **1.666 no las ha leído nadie más**:

| Fichero | Líneas | Estado |
|---|---|---|
| `herramientas/verifica_pieza.py` | 1.177 | **sin revisar** |
| `herramientas/scaffold_pieza.py` | 489 | **sin revisar** |
| `herramientas/lib/arbol.py` | 120 | sin revisar |
| `herramientas/lib/sonda_overflow.js` | 131 | sin revisar |
| `herramientas/verificar_datos.py` | +48/−1 | revisado: el auditor leyó el diff y probó el arreglo |
| `assets/interactives.{js,css}` | 490 | retirados en `df4ce7e` sin llegar a usarse |

Ninguno toca las doce piezas publicadas, así que no bloqueaba el envío. **Pero el día que
alguien se apoye en `verifica_pieza.py` creyendo que pasó por alguna comprobación, se
estará apoyando en esto.** La regla de la casa —quien escribe una pieza no puede ser quien
la valida— vale igual para las herramientas que deciden si una pieza está bien.

Lo que sí está comprobado, por dos personas por separado: los cinco verificadores dan los
mismos números (74 cifras · 0 fallos · 235 sin declarar · 13 páginas EN · 0 ERROR · 120
inyecciones cazadas), y el arreglo del fallo que hacía que `verificar_datos.py` reventara
dejando piezas sin mirar funciona: ahora nombra la que falla y dice «La pasada está
incompleta: esto NO es un verde».

### Y la trampa que vino firmada

Del chat que construyó el gate, con sus palabras:

> «Hoy he escrito dos comprobadores que daban por buena una protección sin medirla —el que
> aceptaba `_redirects` y, cuatro horas antes, el control que se conformaba con cualquier
> fallo en vez de exigir uno nuevo—. Es exactamente el error que este proyecto lleva un mes
> pagando, y lo he cometido **dentro de la herramienta escrita para impedirlo**.»

Que el fallo aparezca dentro del aparato construido para cazarlo no es un descuido: es la
forma que tiene este error de colarse. Por eso el gate exige que el control positivo salte
**en la misma ejecución**, y por eso un código de salida `2` pesa más que un `1`.
