/* Sonda de desbordamiento horizontal. Se inyecta con `agent-browser eval`.
   Devuelve JSON: {sw, cw, culpables:[...]}.

   POR QUÉ NO BASTA scrollWidth === clientWidth
   assets/periodismo.css:49 declara `html,body{overflow-x:hidden}`. Con eso,
   documentElement.scrollWidth SIEMPRE es igual a clientWidth: el navegador
   recorta en vez de crecer. La medida global da verde por construcción y no
   mide nada. Lo dice el propio CLAUDE.md:202-205 («html{overflow-x:hidden}
   enmascara el problema») y aquí está el CSS que lo hace.

   Así que lo que se busca es el elemento recortado: uno que se sale del
   viewport y NO cuelga de un contenedor con scroll propio.

   QUÉ NO ES UN FALLO
   Una tabla ancha dentro de `.data-table-wrap{overflow-x:auto}` se sale a
   propósito y se puede leer arrastrando. Eso es el patrón correcto del repo
   (periodismo.css:296). Por eso se sube por los ancestros: si alguno tiene
   overflow-x auto o scroll, el contenido es alcanzable y no se reporta.

   DOS CRITERIOS, PORQUE UNO SOLO SE ESCAPA
   A · La CAJA se sale del viewport (un div de 1200px, un margen negativo).
   B · La caja cabe, pero su CONTENIDO se sale de ella y lo recorta el
       `html{overflow-x:hidden}` del sitio, sin que nadie lo haya decidido.
   El criterio B se añadió porque el A se escapó en una prueba real: un <pre>
   de 400 caracteres daba rect [0,375] —cabe— con scrollWidth 4214. El texto
   estaba recortado y no había forma de leerlo. Con solo el criterio A, la
   sonda decía «0 culpables» sobre una página con 3.839 px de texto perdido.

   DÓNDE ESTÁ LA LÍNEA DEL CRITERIO B, Y CUÁNTO COSTÓ ENCONTRARLA
   La primera versión exigía `overflow-x` visible U OCULTO, y sobre las doce
   piezas publicadas dio doce falsos positivos:

     · `div#cafe-cup` (cw 88, sw 105, overflow-x:hidden). Lo que se sale es el
       asa de la taza, y el `hidden` está puesto a mano por quien la dibujó.
       Recortar ahí es la decisión, no el fallo.
     · Tres `<text>` de SVG («TAZAS DE CAFÉ AL DÍA», cw 221, sw 230). Dentro de
       un SVG el recorte lo manda el viewBox, no el scrollWidth: los tres se
       ven enteros en pantalla y la sonda los cantaba igual.

   Así que la línea es esta: se señala lo que el autor NO eligió recortar.
   `overflow-x:hidden` es una elección explícita y se respeta; `visible` no lo
   es —es el valor por defecto— y ahí el recorte lo hace el CSS global sin que
   nadie lo haya pedido. Y dentro de un SVG no se mira nada. */
(function () {
  var d = document.documentElement;
  var W = d.clientWidth;
  var TOL = 1;                       // subpíxel de redondeo
  var out = { sw: d.scrollWidth, cw: W, culpables: [] };

  function decideElAutor(el) {
    /* ¿Hay un ancestro que ya haya tomado una decisión sobre este desborde?

       · auto / scroll → el contenido es alcanzable arrastrando. Es el patrón
         correcto del repo para tablas anchas (.data-table-wrap).
       · hidden        → el autor ha decidido recortar ahí. Es lo que hace
         `div#cafe-cup` con el asa de la taza, y no es un descuido.

       Se para en <body> y en <html> a propósito: ahí el `overflow-x:hidden`
       es el guardarraíl global de periodismo.css:49, no una decisión sobre
       este elemento. Si contase, esta sonda no encontraría nunca nada. */
    var p = el.parentElement;
    while (p && p !== document.body && p !== d) {
      var ox = getComputedStyle(p).overflowX;
      if (ox === "auto" || ox === "scroll" || ox === "hidden") return true;
      p = p.parentElement;
    }
    return false;
  }

  function nombre(el) {
    var n = el.tagName.toLowerCase();
    if (el.id) n += "#" + el.id;
    if (typeof el.className === "string" && el.className.trim()) {
      n += "." + el.className.trim().split(/\s+/).slice(0, 2).join(".");
    }
    return n;
  }

  var els = document.querySelectorAll("body *");
  var vistos = {};
  for (var i = 0; i < els.length; i++) {
    var el = els[i];
    if (el.tagName === "SCRIPT" || el.tagName === "STYLE") continue;
    var r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;

    var motivo = null;
    if (r.right > W + TOL || r.left < -TOL) {
      motivo = "la caja se sale del viewport";
    } else if (el.clientWidth > 8 && el.scrollWidth - el.clientWidth > 2 &&
               !el.ownerSVGElement && el.tagName !== "svg") {
      // clientWidth > 8 y no > 0: los enlaces de salto y el texto para
      // lectores de pantalla se ocultan con cajas de 1x1 px y clip
      // (periodismo.css:74-75), y su scrollWidth siempre desborda esa caja.
      // Con «> 0» la sonda señalaba a.skip-link en TODAS las páginas del
      // sitio. Un detector que salta con todo es tan inútil como uno que no
      // salta nunca.
      // Solo cuenta si el propio elemento no puede desplazarse: si tiene
      // overflow-x auto o scroll, el contenido es alcanzable.
      // Solo `visible`: si el autor puso auto/scroll el contenido es
      // alcanzable, y si puso hidden es que ha decidido recortarlo.
      //
      // Y solo si el desborde LLEGA al borde de la pantalla. Un elemento puede
      // salirse de su caja unos píxeles y seguir entero dentro del viewport:
      // en `crisis-memoria-ia` la barra `.cmp-axis-track` mide 167 y su
      // contenido 173, pero acaba en x=295 con la pantalla en 375, así que el
      // rótulo «600%» se lee perfectamente. Sin esta condición la sonda
      // señalaba como recortado algo que no se recorta.
      var derrame = el.scrollWidth - el.clientWidth;
      if (getComputedStyle(el).overflowX === "visible" && r.right + derrame > W + TOL) {
        motivo = "el contenido se sale de la caja y lo recorta el borde de la pantalla";
      }
    }
    if (!motivo) continue;
    if (decideElAutor(el)) continue;
    var k = nombre(el);
    if (vistos[k]) continue;         // no repetir cien celdas de la misma tabla
    vistos[k] = 1;
    out.culpables.push({
      que: k,
      motivo: motivo,
      izq: Math.round(r.left),
      der: Math.round(r.right),
      exceso: motivo.charAt(0) === "l"
        ? Math.round(Math.max(r.right - W, -r.left))
        : el.scrollWidth - el.clientWidth
    });
    if (out.culpables.length >= 10) break;
  }
  return JSON.stringify(out);
})()
