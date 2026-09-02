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

## Estado · actualizado el 2 de septiembre de 2026 (3.ª tanda del día)

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

**12 piezas publicadas.** De los 52 hallazgos documentados: 20 aplicados, 6 cerrados
con hueco declarado, 1 retirado, 1 abierto, 1 sin acción y **23 pendientes**.

**El número que manda: 18 BLOQUEA.** Es el subconjunto de los pendientes que dejaría
a Pablo en evidencia si un jefe de sección lo comprueba — atribuciones fabricadas,
cifras falsas en superficie visible (titular, dek, metadatos, gráficos) y
derivaciones presentadas como dato publicado. Los otros 5 pendientes no bloquean:
3 son matices (B46, B50, B55) y 2 son caducidad programada (B57, B58).

**Cinco piezas están a cero y se pueden enlazar hoy:** `casio-encogerse`,
`dijeron-que-no`, `tim-cook-apple`, `argentina-milei` y `luz-roja`.

| Pieza | BLOQUEA | | Pieza | BLOQUEA |
|---|---|---|---|---|
| caida-gopro | 3 | | cafe-salud | 2 |
| apple-upgrade | 3 | | musk-ceguera | 2 |
| crisis-memoria-ia | 3 | | narcolepsia-orexina | 2 |
| cultura-financiera | 3 | | casio-encogerse | **0** |
| **luz-roja** | **0** | | dijeron-que-no | **0** |
| **argentina-milei** | **0** | | tim-cook-apple | **0** |

**La regla, con número detrás:** Pablo puede escribir a un medio **enlazando solo las
piezas que estén a cero**. Mientras el total de BLOQUEA no sea 0, no se enlaza el
resto ni se manda la web entera.

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
