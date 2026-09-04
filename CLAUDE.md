# Manual de operación · piezas.elur.es

Este archivo lo lee Claude Code al arrancar en este repo. Es la memoria del proyecto.
Manténlo actualizado cuando algo cambie.

---

## Quién es Pablo y qué está haciendo

Pablo González García. Graduado en Periodismo por la USC (2021-2025), matrícula de
honor en Política. Autónomo en Redondela-Vigo: fotógrafo deportivo de patinaje
artístico y fotógrafo gastronómico (marca ELUR). Antes: comunidad de 80.000
seguidores en TikTok, dos años de contenido semanal para una marca de ropa.

**`piezas.elur.es` es su portfolio de periodismo visual con datos, y existe para que
lo contrate un medio.** Todo lo que se hace aquí se juzga por eso.

Objetivo laboral: prácticas bien remuneradas, ~25 h semanales, 600-1.200 €,
facturando como autónomo. Medios gallegos primero (se mueve por Pontevedra, puede ir
un par de días a Santiago, el resto teletrabajo), después unidades de datos
nacionales. CV en `~/Desktop/ADMINISTRACION/CV Pablo Gonzalez v2.pdf`; web personal
en `pablogonzalez.elur.es`.

---

## Cómo trabajar con él

- **Español, directo y conciso. Sin relleno.** Si puedes quitar palabras sin perder
  el sentido, quítalas.
- **Antes de algo grande o irreversible: resume el plan y espera su «ejecuta».**
- **Nunca envíes correos ni mensajes, publiques, borres archivos ni muevas dinero**
  sin confirmación explícita suya.
- **Verifica antes de afirmar.** Prefiere un «no está completo» honesto a un «listo»
  falso. Si dices que algo está hecho, compruébalo.
- **Nunca toques los originales** (fotos, vídeo, facturas) sin avisar: trabaja por copia.
- Si te bloquea un dato que no tiene, **déjale una hoja de ruta** para retomar sin
  que él tenga que repreguntar.
- **Exígele.** No es un cliente al que dar la razón: quiere que le discutas las
  decisiones flojas y le señales lo que no funciona. Si algo está mal, díselo.

### El push es siempre suyo

**No hagas nunca `git commit` ni `git push`.** Deja los cambios en el árbol de
trabajo. Pablo publica haciendo doble clic en `~/Desktop/SUBIR_PIEZAS.command`.
Cuando termines, dile qué archivos ha de subir.

### El historial anterior NO está perdido

El 28 de agosto de 2026 un proceso ajeno reinició la historia del repo. `main`
arrancó de cero y los ocho commits anteriores quedaron **huérfanos**: fuera de la
historia de `origin/main`, pero con los objetos vivos en el servidor. No estaban
borrados, y el error fue darlos por muertos: en GitHub la página del commit carga
entera, con su diff.

Recuperados y fijados el 31 de agosto de 2026:

```
git fetch origin fce001405f8e03048a9559a0428843a9971952af
git tag historial-anterior fce001405f8e03048a9559a0428843a9971952af
```

`historial-anterior` apunta a `fce0014` (28-ago-2026) y arrastra la cadena entera
hasta `5e1c7eb`, la publicación original: ocho commits del 19 al 28 de agosto.
Comprobado con `git log historial-anterior`.

**La etiqueta es local.** Protege los objetos en este portátil, no en GitHub: para
que el servidor deje de considerarlos recogibles hay que empujarla
(`git push origin historial-anterior`), y eso lo decide Pablo. Si algún día el
fetch por SHA falla —GitHub no siempre sirve objetos inalcanzables—, el zip sigue
funcionando:
`github.com/pabloglezjpg/elur-piezas/archive/fce001405f8e03048a9559a0428843a9971952af.zip`

**No toques la historia.** Es de Pablo.

---

## La regla que este proyecto aprendió por las malas

**Quien escribe una pieza no puede ser quien la valida.**

Durante semanas el mismo asistente escribió y revisó las piezas. Una auditoría
externa con dieciséis subagentes encontró **97 hallazgos de gravedad ALTA** en doce
piezas publicadas. Ningún checklist interno había cazado uno solo.

Ejemplos reales, todos de piezas ya publicadas:

- Se escribió «el precio subió 10,8%, el volumen cayó 9,6%, los ingresos subieron
  4,4%». Nadie multiplicó: 1,108 × 0,904 = 1,0016, o sea +0,2%. El párrafo se
  contradecía a sí mismo y estuvo publicado.
- Se dio como inflación acumulada 2000-2025 un 74,1% heredado de una ronda anterior.
  El dato oficial del INE era **83,4%**. Sostenía el cálculo central de la pieza.
- Se presentó un margen del 16,1% como dato de informe. Era una **estimación propia**
  con dos supuestos no declarados. El dato real (11,1%) invertía la conclusión.
- Se afirmó que el máximo histórico de facturación de Casio fue marzo de 2016
  (352.258 M¥). El real es marzo de 2010: **427.925 M¥**. Nadie abrió ese informe.
- Un pie de gráfico decía «Fuente: INDEC» sobre cifras que eran de la UCA.

**Conclusión operativa: cuando escribas, asume que te vas a equivocar y monta la
comprobación fuera de ti.** Y cuando audites lo que escribió otro, no arregles
datos: repórtalos con la fuente que los desmiente.

### Cómo se prueba un verificador: con ficheros reales, no con casos de laboratorio

**El ejemplo que hay que recordar es este: «28 de agosto de 2026».**

El verificador de la edición inglesa buscaba castellano por las tildes. Es lo
razonable, y es lo que se le ocurre a cualquiera. Pero «28 de agosto de 2026» **no
lleva ni una tilde**, así que una fecha en castellano entera —una de las siete capas
que había que traducir— era invisible para él. Las doce piezas salían limpias.

No lo destapó ninguna lista de reglas ni ningún caso de laboratorio. Lo destapó
**inyectar errores en los ficheros publicados**: seis inyecciones en cada una de las
doce piezas, 72 en total, exigiendo que el verificador cazara cada una. Se escapó
trece veces. Un caso sintético no lo habría encontrado nunca, porque un caso
sintético lo escribe quien ya sabe qué está buscando.

De la misma tanda salió el segundo: una portada española colada en `og:image` solo
saltaba de rebote, por el JSON-LD. La pieza que no tiene esa clave —
`casio-encogerse`— pasaba limpia.

**Las dos normas que quedan:**

1. **El control positivo se hace sobre los ficheros reales**, no sobre ficheros de
   prueba. Copia, rompe la copia, exige que salte.
2. **Un detector que salta con todo es tan inútil como uno que no salta nunca.**
   Calíbralo con casos correctos conocidos antes de fiarte: aquí dieron falso
   positivo un DOI (`10.1016/j.tjnut.2025.05.004`), un p-valor español correcto
   (`p < 0,001`), un `hreflang="es"` legítimo, una cita marcada en francés y la
   palabra inglesa «cliché». Los cinco eran correctos; el que se equivocaba era el
   escáner.

---

## Las cinco reglas duras de datos

1. **Si la calculaste tú, dilo.** Toda cifra derivada —un margen sacado dividiendo
   dos cifras, un deflactado, una media, un desglose que el organismo no publica—
   va marcada como cálculo propio. Nunca junto a cifras oficiales sin distinguirla.
2. **Si la traes de antes, vuelve a la fuente.** Una cifra verificada hace tres
   semanas no está verificada hoy. Especialmente: deflactores, índices con base
   móvil, capitalizaciones, rankings, cuotas de mercado, quién ocupa un cargo, y
   todo lo descrito como «el último dato disponible».
3. **Comprueba la aritmética de tus propias frases.** Si en un párrafo hay tres
   porcentajes que se relacionan, multiplícalos.
4. **Fuente primaria es quien genera el dato.** Un medio que reproduce un informe no
   lo es. Un agregador tampoco.
5. **Ninguna afirmación puede contradecir al pie de verificación de su propia pieza.**

### Errores de origen que ya han entrado aquí

- Tasas de propiedad de vivienda presentadas como composición de la riqueza.
- Mezclar Eurostat con estadísticas nacionales en la misma tabla (España e Italia de
  Eurostat, Francia del INSEE, Alemania del censo: no son comparables).
- Umbrales regulatorios atribuidos a organismos que nunca los fijaron. El «umbral de
  riesgo del 35% del Banco de España» no existe; el suyo es el 30%.
- Folclore empresarial: cifras redondas y anécdotas demasiado limpias sostenidas
  solo por blogs y agregadores. Ejemplo: «Yahoo rechazó Google por un millón en
  1998» — todas las fuentes son secundarias; lo documentado es Excite, no Yahoo.
- Empresas japonesas que traducen mal sus propias cifras: 万台 (diez mil unidades)
  aparece como «mil. units» en sus PDF en inglés. Error de factor cien.
- La misma empresa nombrando su ejercicio fiscal de dos maneras. Escribe siempre
  «el ejercicio cerrado en [mes] de [año]», nunca «FY20XX».
- Rupturas de serie que fabrican tendencias falsas (cambios de definición, base o
  clasificación). El paro español de 2000-2001 es el ejemplo clásico.

---

## Anatomía del repo

```
elur-piezas/
├── index.html              portada: destacada + lista + ItemList JSON-LD
├── sitemap.xml  robots.txt
├── <slug>/index.html       una carpeta por pieza
├── <slug>/portada.jpg      1200×630, og:image
├── assets/
│   ├── periodismo.css      sistema visual compartido
│   ├── graphics.js         utilidades de gráfico
│   ├── <pieza>.js          JS específico cuando hace falta
│   └── fonts/              Fraunces, Newsreader, IBM Plex Mono (woff2)
├── herramientas/
│   ├── hacer_portada.py    genera portada.jpg con las fuentes reales
│   └── tiempo_lectura.py   norma de la casa: 225 ppm
└── gracias/                landing de alta en newsletter
```

**Sistema visual:** papel crema `#F4EFE4`, tinta `#191510`, acento rojo teja
`#B84A2C`, filete `#D6CDBC`. Display Fraunces, cuerpo Newsreader, datos IBM Plex
Mono. Columna de lectura 66ch, retícula editorial de una columna, móvil primero.
Sin degradados, sin sombras pesadas.

**Herramientas — úsalas, no hagas las cosas a mano:**
- `python3 herramientas/tiempo_lectura.py --aplicar` — recalcula el tiempo de
  lectura y lo deja igual en la pieza y en su tarjeta. **Nunca lo pongas a mano.**
- `python3 herramientas/hacer_portada.py <slug>` — genera la portada. Requiere las
  fuentes convertidas de woff2 a ttf en `/tmp/fonts` (ver cabecera del script).

---

## Reglas técnicas de cada pieza

1. **Móvil primero. Cero desbordamiento horizontal a 375, 768, 1024 y 1280 px.**
   Medible: `document.documentElement.scrollWidth === clientWidth`. Mide sobre todos
   los elementos del DOM, no solo el body: `html{overflow-x:hidden}` enmascara el
   problema.
2. **La pieza se lee entera sin JavaScript, gráficos incluidos.** Pruébalo generando
   una copia sin los `<script src>`. Controles interactivos ocultos **por ID**:
   `#pieza .needs-js{display:none}` / `#pieza.ready .needs-js{display:revert}`.
3. **Sin CDN externos** (CSP).
4. **SEO completo:** `lang="es"`, title, meta description ≤158, canonical, Open Graph
   con `og:image` 1200×630 y dimensiones declaradas, Twitter Card, JSON-LD `Article`
   con author «Pablo González» y `dateModified`. Alta en `sitemap.xml` y en la portada.
5. **Ninguna cifra del texto puede contradecir a su gráfico.**

### Gotchas que ya han mordido aquí

1. **Nunca `var()` en atributos de presentación SVG** (`fill="var(--x)"`): en Safari
   el fill inválido cae a negro y el stroke a `none`. Usa hex o clase CSS.
2. Drop-cap solo en el primer párrafo: resetea `::first-letter` en todos los `.body`
   y re-aplícalo en `.body:first-of-type`.
3. `min-width:0` en los SVG que deban caber en móvil.
4. `list-style:none` si usas `<ol>` junto a elementos con marcadores propios.
5. El `IntersectionObserver` de reveal deja `opacity:0` el primer frame; si no
   dispara, el contenido desaparece para siempre. Con JS activo, comprueba que
   realmente se revela.
6. **`toLocaleString('es-ES')` NO agrupa los números de cuatro cifras:** 6600 no se
   convierte en 6.600. Ya ha mordido dos veces.
7. Colisiones de nombres de clase entre el CSS de una pieza y el compartido.

---

## Norma tipográfica

Zanjada con la *Ortografía de la lengua española* de la RAE, § 3.4.1.2.

| Elemento | ¿Punto final? |
|---|---|
| Titular, antetítulo, ladillos, títulos de gráfico | **NUNCA** (§ 3.4.1.2.1) |
| Dek | **SÍ**, si tiene dos o más frases o puntuación interna |
| Pie de gráfico | Etiqueta corta no; explicación oracional sí |
| Teaser de portada | Sí |

**El dek no es el «subtítulo» de la RAE.** Ese es la segunda mitad de un título;
un dek periodístico es discursivo. Titular sin punto y dek con punto **no es
incoherencia**.

Castellano de España. Miles con punto, decimales con coma, porcentaje pegado al
número: 90%.

### Comillas: nunca rectas, en ningún idioma

| Edición | Cita | Apóstrofo |
|---|---|---|
| Español | `«…»` | `’` |
| Inglés | `“…”` | `’` |

**Una comilla recta (`"` o `'`) es siempre un descuido aquí.** No es un error de
idioma: es texto sin maquetar, y Pablo le vende cuidado tipográfico a redacciones.
La edición española lleva 129 guillemets y **cero** rectas desde el principio; la
inglesa nació con tres convenciones a la vez —guillemets en dos piezas, tipográficas
en una y rectas en nueve— y se unificó el 3 de septiembre de 2026.

Dos cosas que enseñó esa unificación:

- **Las comillas viven también en los metadatos.** Al convertir solo el cuerpo
  quedaron 28 apóstrofos rectos en `content=""`, `alt` y JSON-LD, diciendo
  `wasn't` donde el cuerpo ya decía `wasn’t`. Es el fallo de siempre: corregido en
  el cuerpo y no en las otras ocho superficies. Convierte las dos capas o ninguna.
- **Una cita en otro idioma lleva las comillas del texto que la envuelve.** El
  francés de `cultura-financiera` estaba como `<span lang="fr">«…»</span>`; ahora
  las comillas van fuera del span y son inglesas, porque son puntuación de la frase
  inglesa. El span solo contiene francés.

Lo vigila `verificar_en.py`, y el guillemet entra ahí por una razón incómoda: es
probablemente el signo más inequívocamente español que existe y el escáner lo
dejaba pasar entero. Tercer agujero de la familia de las fechas.

**Nunca conviertas comillas con un `sed` sobre el fichero.** Las rectas son
obligatorias en los atributos HTML y en el JSON-LD. Hay que trocear el documento y
tocar solo los nodos de texto; y para decidir si una comilla abre o cierra, usa dos
métodos independientes —alternancia y contexto— y aborta si discrepan.

---

## La voz de Pablo

**No conviertas su texto en prosa de IA.** Este portfolio existe para demostrar cómo
escribe él. Seca, directa, concreta, sin relleno. Frases cortas. Nada de tribuna.

Fuera: «cabe destacar», «no es baladí», «en un mundo cada vez más», «resulta
fundamental», «se erige como». Si dudas entre una frase tuya más elegante y una suya
más torpe pero con carácter, **deja la suya**.

**Tics detectados que hay que romper:** «Aquí te contamos» (en 5 de 12 piezas), «la
pregunta útil no es X sino Y» (12 veces en 8 piezas), «Cierre» como ladillo (7 de
12), cierre aforístico (12 de 12). Eso no es voz común: es plantilla.

---

## Estado · actualizado el 4 de septiembre de 2026 (auditoría externa aplicada)

> **Esta sección caduca sola.** Si la fecha de arriba no es la de hoy, no te fíes de
> los números: vuelven a contarse solos. La verdad viva está en tres sitios, y los
> tres se consultan en un minuto:
>
> - `python3 herramientas/coherencia_metadatos.py` — puerta de metadatos. Sale con 1
>   si hay ERROR o si la cobertura baja respecto a `herramientas/superficies.json`.
> - `~/Desktop/auditoria-piezas-2026-08-28/RETENIDOS-B07-B58.md` — los 52 hallazgos.
> - `git status` — lo que está sin publicar.
>
> **Quien cierre una tanda actualiza esta sección y le cambia la fecha, o la borra.**
> Una sección de estado caducada ya provocó una contradicción entre dos chats.

**12 piezas publicadas.** De los 52 hallazgos documentados: 38 aplicados, 9 cerrados
con hueco declarado, 1 retirado, 1 abierto, 1 sin acción y **2 pendientes**, que son
las dos caducidades con fecha (B57 el 9 de septiembre, B58 el 24).

# BLOQUEA: 0

Las doce piezas están a cero. Es el número que decide si Pablo puede escribir a un
medio: cuenta las cifras falsas en superficie visible, las atribuciones fabricadas y
las derivaciones presentadas como dato publicado. Los tres pendientes que no bloquean
son matices (B46, B50, B55).

**Aviso de calendario:** el keynote de Apple es el **miércoles 9** y caduca
`apple-upgrade` entera (B57). Esa pieza necesita una segunda pasada de actualización
de datos el 9 por la tarde o el jueves 10 — no de corrección, que ya está hecha.

### Auditoría externa del 4 de septiembre: las seis piezas bloqueadas

Un chat auditor abrió 183 afirmaciones en su fuente primaria y 31 fallaron. Seis
piezas quedaron marcadas «no enlazar», y eran casi exactamente las seis que abren
los veintinueve correos. **Las seis están cerradas.** Todas las cifras se
reverificaron abriendo la fuente, no leyendo el informe.

| Pieza | Qué fallaba | Qué dice la fuente |
|---|---|---|
| `caida-gopro` | cerraba preguntando quién compraría GoPro | 8-K del 1-9-2026: fusión con Starman Optical. 285 M$, 1,14 $/acción, **y los accionistas conservan ~10%**; sigue en el Nasdaq; **no está cerrado** |
| `dijeron-que-no` | ×6.600 · patente de Sasson «expira en 2007» · cita atribuida a Blockbuster | 333.000÷50 = **6.660** · Google Patents: **20-5-1997** (20 años desde la presentación, regla GATT) · es paráfrasis de McCarthy, y Antioco lo niega |
| `casio-encogerse` | 44% de relojería «del ejercicio» · «China bajó un 3% en el ejercicio» | dossier S25 p. 33: el 44% es el **4T**; el ejercicio es **47,8%** · dossier S26 p. 8: el −3% es **4T, relojería, moneda local** |
| `cultura-financiera` | el 19% atribuido al informe de la ECF 2021 | **no está en sus 60 páginas** (su único 19% es de vehículos de ahorro, p. 30). Está en la **diapositiva 10** de la presentación del BdE (Arce y Gavilán, 14-11-2023) |
| `musk-ceguera` | «formas y letras a dos personas» · DOI muerto | *Science Advances* 2025 = **dos** personas, fosfenos, sin letras · las letras son *JCI* 2021, **una** participante · el DOI declarado daba **404** |
| `argentina-milei` | «dólar oficial ≈1.400 → ≈1.700» · pobreza trimestral atribuida al INDEC | API del BCRA: **391** y **1.531**; el **máximo histórico es 1.533,63** · el INDEC no publica pobreza trimestral: retirada con hueco declarado |

**El patrón, y es uno solo:** una cifra que se mueve, congelada en el escaparate y
sin fecha. Pasaba con el 99,4% de GoPro, el «0,60 $ **hoy**» de su portada, el
«lo que vale Netflix **hoy**» de la de Netflix y el ≈33% de Argentina.

> **La regla que faltaba, y ahora es de la casa:** toda cifra que se mueva lleva su
> fecha pegada **en la superficie donde se publique**, no solo en el gráfico. «El
> 99,4% que perdió hasta agosto de 2026» no caduca. «Ha perdido el 99,4%» caduca
> cada día.

### Lo que el verificador no ve, medido

El auditor le inyectó **84 errores y cazaba 27**. Arreglados los dos suyos —el
signo y la pieza que desaparece— **caza 35**. Los dos agujeros:

- **No distinguía el signo.** La frontera de `aparece()` excluía dígito, punto y
  coma, pero no el signo, así que «−99,4%» y «+99,4%» eran la misma cifra. En una
  pieza titulada con una caída del 99% ese es el error más caro que existe. Ahora
  el manifiesto acepta `"signo": "negativo"|"positivo"` y se comprueba.
- **Salía con éxito si desaparecía una pieza.** `coherencia_metadatos.py` filtraba
  la línea base a las piezas que estaba mirando **antes** de comparar, así que la
  rama «ya no se comprueba» no podía dispararse. Ahora solo filtra cuando se pide
  una pieza suelta.

**Los dos verificadores se cubren mutuamente y hay que correr los dos:** borrar una
pieza entera lo caza `coherencia_metadatos.py`; borrar solo su `datos.json` lo caza
`verificar_datos.py`. Ninguno solo cubre los dos casos.

**De las 49 que aún se escapan, cuatro son imposibles por diseño** y conviene no
prometerlas: la mentira coherente (cambiar la cifra en el manifiesto *y* en todas
las superficies), la permutación de dos valores, y las dos en que el cuerpo
contradice a su propio pie. `verificar_datos.py` compara la pieza **consigo misma**,
no con el mundo: puede dar «0 fallos» mientras GoPro se fusiona.

### La edición inglesa

**Las doce piezas existen en inglés**, en `<slug>/en/index.html`, más un índice propio
en `en/index.html` con sus doce tarjetas y su ItemList. Cada pieza tiene su
`portada-en.jpg`: antes las dos versiones de una pieza compartían la portada
española, así que un editor anglófono pegaba el enlace en Slack y le salía una
tarjeta en castellano, con puntuación española.

Lo que cambia entre versiones no es solo el texto. Son siete capas, y las siete
han fallado alguna vez en este proyecto:

1. **Texto visible**, escrito en inglés, no traducido palabra a palabra.
2. **Cifras**: `99,4%` → `99.4%`, `1.093,5` → `1,093.5`. Incluidos los nodos que
   son SOLO un número —etiquetas de SVG, celdas de tabla—, que es justo lo que se
   escapa cuando el extractor descarta lo que no parece texto.
3. **Fechas**: `28 de agosto de 2026` → `28 August 2026`; `18-ago-2026` → `18 Aug 2026`.
4. **Atributos**: `alt`, `title`, `aria-label`, y `<title>`/`<desc>` dentro del SVG.
5. **JSON-LD entero**, `inLanguage` incluido y `mainEntityOfPage.@id` a la URL `/en/`.
6. **`canonical`, `og:url` y `hreflang`** en los dos sentidos.
7. **La portada social**, que es la única que no vive en el HTML.

**El JS también habla.** Cinco ficheros de `assets/` escribían texto en castellano
desde JavaScript y ahora conmutan por `document.documentElement.lang`, igual que
`formato.js`: `apple-upgrade.js`, `cultura-financiera.js`, `cafe-salud.js`,
`musk.js`. Si añades una pieza con JS que escriba texto, hazlo bilingüe desde el
principio.

**`Formato.moneda` cambia el símbolo de sitio, no solo el separador.** En español
va detrás y separado (`1.099 $`), en inglés delante y pegado (`$1,099`), y el signo
negativo queda fuera del símbolo (`−$331.24`). Está en `assets/formato.js`, que es
la fuente única.

`python3 herramientas/verificar_en.py` recorre las trece páginas inglesas y falla
con código 1. Cubre las siete capas y además coteja cada cifra contra el
`datos.json` de la pieza española y exige que el `portada-en.jpg` exista de verdad,
sea un JPEG y no una portada española colada.

**Lo que enseñó el control positivo, y por qué no basta con `--autotest`.** El
escáner daba las doce piezas limpias. Al inyectar errores en los ficheros reales
—seis por pieza, 72 en total— se vio que **las fechas en castellano no las miraba
nadie**: «28 de agosto de 2026» no lleva ni una tilde, y la única defensa contra el
castellano era buscar tildes. Y que una portada española en `og:image` solo saltaba
de rebote por el JSON-LD, así que `casio-encogerse`, que no tiene esa clave, se
colaba. Los dos agujeros están tapados y el control vive en el guion que los
destapó. **Un verificador que da limpio a la primera no está probado: está sin
probar.**

### El rótulo dice PIEZAS, también en inglés

Decisión de Pablo del 3 de septiembre de 2026, después de haberlo unificado primero
en el otro sentido. **El sitio se llama PIEZAS en las dos ediciones**: es el dominio
y es la marca, y un medio no traduce su cabecera — nadie llama «The World» a *Le
Monde*. «Pieces» sobre un enlace a `piezas.elur.es` deja el nombre desalineado con
la URL que el lector tiene en la barra.

Con eso, las cuatro superficies del nombre dicen lo mismo por primera vez: el rótulo
visible, `og:site_name`, los títulos y `image:alt` del índice, y las once portadas
sociales que lo dibujan.

**El rótulo ya no es un literal.** Vivía escrito a mano en tres maquetas distintas de
`hacer_portada.py`, y por eso pudo quedarse partido entre idiomas. Ahora es la
constante `MARCA` y el ayudante `marca()`, que dibujan las cuatro maquetas con
rótulo (`panel` no lleva). Una pieza puede sobreescribirlo con `"marca"` en su
configuración; piénsalo dos veces antes de usarlo. El refactor se comprobó
regenerando las 24 portadas antes y después: **idénticas byte a byte.**

### Portadas: tres maquetas nuevas

`hacer_portada.py` tenía dos maquetas y cuatro piezas llevaban su portada como JPG
suelto, sin configuración: nadie podía regenerarlas. Así es exactamente como la
portada de `argentina-milei` se quedó tres días diciendo «300%» después de
corregirse el HTML. Ahora hay tres maquetas más —`ancla`, `cifra` y `panel`— y las
doce piezas se regeneran con un comando.

`panel` no redibuja el gráfico: lo recorta de la portada española de la misma pieza
y solo reescribe su rótulo, para que las dos versiones enseñen la misma imagen y no
dos simulaciones distintas.

### Orden de despliegue

`pablogonzalez.elur.es` enlaza a las doce piezas inglesas. Esos enlaces dan **404
honesto** hasta que se suba `piezas.elur.es`. **Primero piezas, después el
portfolio.**

### El manifiesto de datos

Cada pieza tiene ahora `<slug>/datos.json`: las cifras que viven en más de una
superficie, con su fuente primaria, si es dato oficial o cálculo propio, y en qué
superficies aparece cada una. **49 cifras en las doce piezas.**

`python3 herramientas/verificar_datos.py` comprueba que cada cifra dice lo mismo en
todas sus superficies y falla con código 1 si no. Nace de que todos los errores de
este proyecto tienen la misma forma: un número corregido en el cuerpo y no en las
otras ocho superficies. El «300%» de Argentina siguió tres días en su `portada.jpg`
después de corregirse en el HTML.

**`--autotest` es obligatorio antes de fiarse de él.** Inyecta un error en cada pieza
y exige cazarlo. La primera versión del verificador daba «0 fallos» siendo mentira:
comparaba con `valor in texto`, así que «211,4» seguía estando dentro de «211,49».
Un test que no puede fallar no prueba nada.

### Calendario con reloj

| Fecha | Qué pasa | A qué afecta |
|---|---|---|
| ~~1-sep-2026~~ | ~~Tim Cook deja Apple~~ | **HECHO** el 2-sep con `parche-b56.py`. Once superficies en pasado, `dateModified` 2026-09-02 |
| 9-sep-2026 | Keynote de Apple | `apple-upgrade` (el caso por defecto es el iPhone 17 Pro, congelado en OG), `tim-cook`, `crisis-memoria-ia`. Es B57 |
| 24-sep-2026 | El INDEC publica pobreza del 1S2026 | `argentina-milei`: 19 puntos + portada + `portada.jpg`. Es B58 |
| sin fecha | GoPro puede anunciar su venta | `caida-gopro` tiene un bloque de actualización listo |

### Parches preparados

- `~/Desktop/auditoria-piezas-2026-08-28/parche-b56.py` — **ya aplicado** el 2-sep.
- `~/Desktop/auditoria-piezas-2026-08-28/parche-b36-b37.py` — **ya aplicado** el 31-ago.
  Ambos abortan si el texto no coincide; se pueden volver a lanzar sin riesgo.

---

## Fuera del repo

- **`~/PERIODISMO/`** — el cuaderno de trabajo: borradores, prompts, respuestas a la
  auditoría, hojas de ruta. Ahí vive `TAREAS_PABLO.md`.
- **Notion** — base `PIEZAS` (data source `38c65c74-10fb-4209-8223-b28d7667710e`,
  página madre `PERIODISMO` `3b2d313e-3baa-8155-bd94-d689b0cf6f68`). Cada pieza es
  una ficha con subpáginas de REDACCION y PROMPTS. **Pablo anota en MAYÚSCULAS
  dentro de las fichas: eso son instrucciones suyas y hay que leer la página entera
  antes de trabajar, no solo la parte que parece relevante.**
- **Skills instaladas** que aplican aquí: `nueva-pieza-periodistica`,
  `limpiar-research-pieza`, `editar-pieza-periodistica` (lleva el checklist de cierre
  de 14 puntos), `montar-pieza-visual`, `auditar-piezas-publicadas`.

---

## Flujo de una pieza

1. **Tema** → `nueva-pieza-periodistica`: valida que aguanta, crea la ficha en Notion,
   genera el prompt de Perplexity.
2. **Research** → Pablo lanza Perplexity y trae el volcado → `limpiar-research-pieza`.
3. **Redacción** → v1, y Pablo la reescribe en su voz. **El texto tiene que sonar a
   él.**
4. **Edición** → `editar-pieza-periodistica`, con el checklist de cierre respondido
   punto por punto.
5. **Verificación externa** → alguien que no escribió la pieza. No es opcional.
6. **Montaje** → `montar-pieza-visual` genera los prompts de Design y de Code.
7. **Portada** → `herramientas/hacer_portada.py`.
8. **Alta** → sitemap, portada, ItemList. `tiempo_lectura.py --aplicar`.
9. **Publicación** → la hace Pablo con `SUBIR_PIEZAS.command`.
