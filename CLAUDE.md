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

## Estado a 28 de agosto de 2026

**12 piezas publicadas.** Auditoría externa recién entregada: 101 hallazgos, 97 de
gravedad ALTA. Primera tanda de respuestas ya enviada al auditor.

**Lo más urgente:** los seis hallazgos de atribución de fuente (una pieza atribuye al
INDEC cifras de la UCA). Eso es lo único que un jefe de sección no perdona.

**Confirmados y en corrección en Casio:** el máximo histórico no es 2016 sino 2010
(427.925 M¥, con pérdida operativa de 29.309 — la Casio grande perdía dinero, lo cual
refuerza la tesis); «mejor ejercicio de la década» es falso; el bloque de precio y
volumen falla su propia aritmética; los «nuevos negocios» del Gráfico 3 son en
realidad 非継続事業, negocios discontinuados.

**Regla mientras esto no cierre: Pablo no manda ningún correo a ningún medio.**

### Calendario con reloj

| Fecha | Qué pasa | A qué afecta |
|---|---|---|
| 1-sep-2026 | Tim Cook deja Apple | `tim-cook-apple`: todos los tiempos verbales pasan a pasado, también en la portada |
| 9-sep-2026 | Keynote de Apple | `apple-upgrade` (el caso por defecto es el iPhone 17 Pro, congelado en OG), `tim-cook`, `crisis-memoria-ia` |
| 24-sep-2026 | El INDEC publica pobreza del 1S2026 | `argentina-milei`: todo el panel de pobreza |
| sin fecha | GoPro puede anunciar su venta | `caida-gopro` tiene un bloque de actualización listo |

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
