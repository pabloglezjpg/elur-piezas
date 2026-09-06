/* ============================================================
   piezas.elur.es — interactives.js
   Los interactivos de las piezas, configurados por atributos data-*.

   POR QUÉ EXISTE
   Había seis ficheros sueltos en assets/, uno por pieza, escritos a mano:
   casio.js (48 líneas), milei.js (42), cultura-financiera.js (92),
   cafe-salud.js (185), apple-upgrade.js (263) y musk.js (359). Entre ellos:

     · El mismo grupo pestaña↔panel escrito dos veces. casio.js:25-32 y
       milei.js:26-33 son el mismo código con una sola diferencia real:
       uno oculta con `classList.toggle("is-on")` y el otro con `p.hidden`.
     · La detección de idioma —`/^en/i.test(document.documentElement
       .getAttribute("lang") || "")`— LITERAL en cinco ficheros.
     · Dos reimplementaciones enteras del formateador de números que
       assets/formato.js existe para evitar (graphics.js:112-115 y
       apple-upgrade.js:56-61).
     · El armazón `piece = getElementById(...)` + `safe()` + `.ready`, seis
       veces.

   EL PATRÓN NO SE INVENTA AQUÍ: YA ESTABA EN EL REPO
   assets/graphics.js ya es exactamente esta librería para su mitad —anima
   por data-grow, data-draw, data-count, data-decimals, data-prefix,
   data-suffix y .reveal, no sabe el nombre de ninguna pieza y respeta
   prefers-reduced-motion—. Esto es lo mismo para los interactivos. Los dos
   conviven: graphics.js anima, interactives.js interactúa.

   LA REGLA QUE NO SE ROMPE
   El DOM ya muestra el ESTADO FINAL. Sin JS la pieza se lee entera, gráficos
   incluidos; los controles solo aparecen cuando la raíz recibe `.ready`. Si
   algo de aquí revienta, la clase no se pone y la pieza se queda en su estado
   estático, legible. Nada de esto es progresivo por cortesía: es la regla 2 de
   las técnicas del repo y hay un gate que la mide.

   LO QUE NO ABSORBE, Y SE DICE
   El simulador de fosfenos en canvas y la escena 3D de `musk-ceguera` son de
   esa pieza y ahí se quedan. Se enganchan aquí con `Piezas.componente()` en vez
   de repetir el armazón, pero dibujar una vía visual en WebGL no es un
   componente reutilizable y fingir que lo es sería mentir sobre la librería.

   USO, UNA LÍNEA POR COMPONENTE
     grupo     <div data-piezas-grupo="metrica"><button data-valor="paro">…
     panel     <div data-piezas-panel="metrica" data-valor="paro">…
     filtro    <ul><li data-piezas-filtrable="fase" data-valor="2">…
     selector  <div data-piezas-grupo="extras" data-multiple><button data-valor="azucar">…
     quiz      <div data-piezas-quiz><div data-pregunta><button data-correcta>…
     rango     <input type="range" data-piezas-rango="phos" …>
     cronómetro<span data-piezas-desde="2016-03-20" data-plantilla="hace {dias} días">
     diferido  <button data-piezas-carga="../assets/three.min.js" data-destino="#via-3d">
   ============================================================ */
(function (global) {
  "use strict";

  var Piezas = {};

  /* ---------- idioma: fuente única, ya no cinco copias ---------- */
  function ingles() {
    return typeof document !== "undefined" &&
      /^en/i.test(document.documentElement.getAttribute("lang") || "");
  }
  Piezas.ingles = ingles;

  /* Elige entre dos cadenas por el idioma del documento. Sustituye a los
     `var EN = ...; EN ? "..." : "..."` repartidos por cuatro ficheros. */
  Piezas.texto = function (es, en) { return ingles() ? en : es; };

  /* Formato: SIEMPRE assets/formato.js. Sin reserva a mano y sin
     toLocaleString, que no agrupa los millares de cuatro cifras (6600 sale
     «6600») y ya mordió dos veces. Si formato.js no está cargado, se devuelve
     el número tal cual y se avisa por consola: mejor un número sin separar que
     un número mal separado que contradiga al gráfico. */
  Piezas.num = function (n, dec) {
    if (global.Formato) return global.Formato.numero(n, dec);
    if (!Piezas._avisado) {
      Piezas._avisado = true;
      if (global.console) console.warn("interactives.js: falta assets/formato.js");
    }
    return String(n);
  };
  Piezas.moneda = function (n, dec, simbolo) {
    return global.Formato ? global.Formato.moneda(n, dec, simbolo) : String(n);
  };
  Piezas.porcentaje = function (n, dec) {
    return global.Formato ? global.Formato.porcentaje(n, dec) : String(n) + "%";
  };

  /* ---------- utilidades ---------- */
  function qsa(sel, raiz) {
    return Array.prototype.slice.call((raiz || document).querySelectorAll(sel));
  }
  function attr(el, n) { return el.getAttribute(n); }

  /* Ejecuta y traga el error: si un componente revienta, los demás siguen y la
     pieza se queda en su estado estático en vez de en blanco. */
  function safe(fn, a, b) {
    try { return fn(a, b); } catch (e) {
      if (global.console) console.warn("interactives.js:", e && e.message);
      return null;
    }
  }
  Piezas.safe = safe;

  /* Registro de componentes de pieza. Un interactivo que la librería no cubre
     —la escena 3D de musk-ceguera— se engancha aquí y hereda el ciclo de vida
     sin repetirlo. */
  var propios = [];
  var yaArrancado = false;

  /* Si la librería ya ha arrancado, el componente se ejecuta en el acto.

     Hace falta porque el fichero de la pieza se carga DESPUÉS de este —los dos
     con `defer`, y defer respeta el orden del documento—, así que cuando llama
     a `componente()` el arranque ya ha pasado y la función se quedaría en la
     lista sin ejecutarse nunca. Pasó con musk-ceguera: el filtro y el resto de
     la librería funcionaban, y el canvas de fosfenos y el contador de días no
     llegaban a montarse. Lo cazó comparar la pieza migrada contra la original. */
  Piezas.componente = function (fn) {
    propios.push(fn);
    if (yaArrancado) safe(fn, Piezas);
  };

  /* ================================================================
     GRUPO · pestañas, filtros y selectores. Es el mismo gesto.

     Un contenedor con botones `data-valor`. Al pulsar, se marca
     aria-pressed y se aplica el efecto sobre los destinos del mismo grupo.

     data-modo:
       "oculta"  (por defecto) panel.hidden = true|false   ← lo de milei.js
       "clase"   alterna la clase .is-on                   ← lo de casio.js
       "atenua"  alterna .dim, sin ocultar                 ← el mapa de musk.js
     data-multiple  el grupo acumula en vez de elegir uno  ← cafe-salud.js
     data-todo      valor que significa «todos»            ← el «all» de musk.js
     ================================================================ */
  function initGrupo(grupo) {
    var nombre = attr(grupo, "data-piezas-grupo");
    var modo = attr(grupo, "data-modo") || "oculta";
    var multiple = grupo.hasAttribute("data-multiple");
    var todo = attr(grupo, "data-todo");
    var botones = qsa("[data-valor]", grupo);
    if (!nombre || !botones.length) return;

    // Un grupo puede no conmutar nada: en `cafe-salud` los botones solo
    // describen lo que hay en la taza y el dibujo lo hace la pieza. Antes esto
    // volvía sin cablear nada y la pieza se quedaba muerta. Si no hay destinos,
    // la librería lleva igual el estado y el aria-pressed, y avisa del cambio.
    var destinos = qsa('[data-piezas-panel="' + nombre + '"]')
      .concat(qsa('[data-piezas-filtrable="' + nombre + '"]'));

    var elegidos = [];

    function aplica() {
      destinos.forEach(function (d) {
        var v = attr(d, "data-valor");
        var on = (todo !== null && elegidos.indexOf(todo) !== -1) ||
                 elegidos.indexOf(v) !== -1;
        if (modo === "clase") d.classList.toggle("is-on", on);
        else if (modo === "atenua") d.classList.toggle("dim", !on);
        else d.hidden = !on;
      });
      botones.forEach(function (b) {
        b.setAttribute("aria-pressed",
          elegidos.indexOf(attr(b, "data-valor")) !== -1 ? "true" : "false");
      });
      // Un contenedor cuyos hijos han quedado todos fuera se retira entero,
      // que es lo que hacía musk.js con los grupos de fase del mapa.
      qsa('[data-piezas-grupo-vacio="' + nombre + '"]').forEach(function (g) {
        g.hidden = !qsa("[data-piezas-filtrable]:not(.dim)", g).length;
      });
      document.dispatchEvent(nuevoEvento("piezas:grupo", {
        nombre: nombre, elegidos: elegidos.slice(), multiple: multiple
      }));
    }

    botones.forEach(function (b) {
      b.addEventListener("click", function () {
        var v = attr(b, "data-valor");
        if (multiple) {
          var i = elegidos.indexOf(v);
          if (i === -1) elegidos.push(v); else elegidos.splice(i, 1);
        } else {
          elegidos = [v];
        }
        aplica();
      });
    });

    // Estado inicial: lo que el HTML ya declara. Sin JS ese es el estado que
    // se ve, así que arrancar en otro sitio haría parpadear la pieza.
    var marcado = botones.filter(function (b) {
      return b.getAttribute("aria-pressed") === "true";
    });
    elegidos = marcado.length
      ? marcado.map(function (b) { return attr(b, "data-valor"); })
      : (multiple ? [] : [attr(botones[0], "data-valor")]);
    aplica();
    grupo._piezasAplica = aplica;
  }

  /* ================================================================
     QUIZ · preguntas de una en una. cultura-financiera.js.
     Sin JS el DOM muestra TODAS las preguntas y sus medias, que es lo que
     hace que la pieza se lea entera; con JS se van pasando.
     ================================================================ */
  function initQuiz(quiz) {
    var preguntas = qsa("[data-pregunta]", quiz);
    var salida = quiz.querySelector("[data-quiz-salida]");
    var reinicio = quiz.querySelector("[data-quiz-reinicio]");
    if (!preguntas.length) return;
    var aciertos = 0;

    function arranca() {
      aciertos = 0;
      preguntas.forEach(function (q, i) {
        q.hidden = i !== 0;
        qsa("[data-valor],[data-correcta]", q).forEach(function (b) {
          b.disabled = false;
          b.classList.remove("chosen", "is-correct", "is-wrong");
        });
      });
      if (salida) salida.textContent = "";
      if (reinicio) reinicio.hidden = true;
    }

    function avanza(q) {
      var i = preguntas.indexOf(q);
      q.hidden = true;
      if (i + 1 < preguntas.length) { preguntas[i + 1].hidden = false; return; }
      if (salida) {
        var plantilla = attr(quiz, Piezas.ingles() ? "data-resultado-en" : "data-resultado")
          || "{aciertos}/{total}";
        salida.textContent = plantilla
          .replace("{aciertos}", Piezas.num(aciertos))
          .replace("{total}", Piezas.num(preguntas.length));
      }
      if (reinicio) reinicio.hidden = false;
      // La pieza puede rematar el mensaje: `cultura-financiera` cambia la
      // frase si se aciertan las tres. La librería no adivina eso.
      document.dispatchEvent(nuevoEvento("piezas:quiz-fin", {
        aciertos: aciertos, total: preguntas.length, quiz: quiz
      }));
    }

    preguntas.forEach(function (q) {
      qsa("button", q).forEach(function (b) {
        b.addEventListener("click", function () {
          qsa("button", q).forEach(function (x) { x.disabled = true; });
          b.classList.add("chosen");
          var bien = b.hasAttribute("data-correcta");
          b.classList.add(bien ? "is-correct" : "is-wrong");
          if (bien) aciertos++;
          else {
            var buena = q.querySelector("[data-correcta]");
            if (buena) buena.classList.add("is-correct");
          }
          global.setTimeout(function () { avanza(q); }, 700);
        });
      });
    });
    if (reinicio) reinicio.addEventListener("click", arranca);
    arranca();
  }

  /* ================================================================
     RANGO · un deslizador que avisa a quien escuche. musk.js (fosfenos).
     La librería cablea el input; lo que se dibuje con el valor es de la pieza.
     ================================================================ */
  function initRango(input) {
    var nombre = attr(input, "data-piezas-rango");
    function emite() {
      var ev;
      try {
        ev = new CustomEvent("piezas:rango", {
          detail: { nombre: nombre, valor: Number(input.value) }
        });
      } catch (e) {                       // navegadores sin constructor
        ev = document.createEvent("CustomEvent");
        ev.initCustomEvent("piezas:rango", true, false,
          { nombre: nombre, valor: Number(input.value) });
      }
      input.dispatchEvent(ev);
      document.dispatchEvent(ev);
    }
    input.addEventListener("input", emite);
    emite();
  }

  /* ================================================================
     CRONÓMETRO · días transcurridos desde una fecha. musk.js (timeline).

     Se calcula en cada carga, nunca se congela. Una promesa de hace tres años
     con el contador escrito a mano miente un día más cada día, y esa cuenta
     era justo el argumento de la pieza.
     ================================================================ */
  function initCronometro(el) {
    var p = (attr(el, "data-piezas-desde") || "").split("-");
    if (p.length !== 3) return;
    var desde = new Date(+p[0], +p[1] - 1, +p[2]);
    var hoy = new Date();
    hoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
    var dias = Math.round((hoy - desde) / 86400000);
    var plantilla = attr(el, Piezas.ingles() ? "data-plantilla-en" : "data-plantilla")
      || "{dias}";
    el.textContent = plantilla.replace("{dias}", Piezas.num(dias));
  }

  /* ================================================================
     CARGA DIFERIDA · un botón que trae un script pesado solo si lo piden.
     musk.js (visor 3D con three.js, 600 KB que no se bajan si nadie pulsa).

     Si el script no carga o el aparato no puede con él, se enseña el aviso de
     `data-aviso` y el botón desaparece: la ilustración estática de arriba sigue
     contando la historia entera.
     ================================================================ */
  function initCarga(boton) {
    var src = attr(boton, "data-piezas-carga");
    var caja = document.querySelector(attr(boton, "data-destino") || "");
    if (!src || !caja) return;
    var cargado = false, visible = false;

    function rotula() {
      var k = visible ? "data-texto-ocultar" : "data-texto-mostrar";
      var t = attr(boton, Piezas.ingles() ? k + "-en" : k);
      if (t) boton.textContent = t;
      boton.setAttribute("aria-expanded", visible ? "true" : "false");
    }
    function falla() {
      caja.hidden = false;
      caja.textContent = attr(boton, Piezas.ingles() ? "data-aviso-en" : "data-aviso")
        || Piezas.texto("No se pudo cargar. La ilustración de arriba lo muestra entero.",
                        "It could not be loaded. The illustration above shows it in full.");
      boton.hidden = true;
    }

    boton.addEventListener("click", function () {
      if (cargado) {
        visible = !visible; caja.hidden = !visible; rotula();
        if (visible) document.dispatchEvent(nuevoEvento("piezas:reanuda", { caja: caja }));
        return;
      }
      boton.disabled = true;
      var s = document.createElement("script");
      s.src = src; s.async = true;
      s.onload = function () {
        boton.disabled = false; cargado = true; visible = true;
        caja.hidden = false; rotula();
        document.dispatchEvent(nuevoEvento("piezas:cargado", { caja: caja, src: src }));
      };
      s.onerror = function () { boton.disabled = false; falla(); };
      document.head.appendChild(s);
    });
    rotula();
  }

  function nuevoEvento(nombre, detalle) {
    try { return new CustomEvent(nombre, { detail: detalle }); }
    catch (e) {
      var ev = document.createEvent("CustomEvent");
      ev.initCustomEvent(nombre, true, false, detalle);
      return ev;
    }
  }
  Piezas.evento = nuevoEvento;

  /* ================================================================
     ARRANQUE
     Una sola raíz `.pieza` recibe `.ready`, y eso es lo que revela los
     controles. Antes cada pieza lo hacía con su propio id y su propio fichero.
     ================================================================ */
  function arranca() {
    qsa("[data-piezas-grupo]").forEach(function (g) { safe(initGrupo, g); });
    qsa("[data-piezas-quiz]").forEach(function (q) { safe(initQuiz, q); });
    qsa("[data-piezas-rango]").forEach(function (r) { safe(initRango, r); });
    qsa("[data-piezas-desde]").forEach(function (c) { safe(initCronometro, c); });
    qsa("[data-piezas-carga]").forEach(function (b) { safe(initCarga, b); });
    yaArrancado = true;
    propios.forEach(function (fn) { safe(fn, Piezas); });

    // `.ready` la última: si algo de arriba revienta, la pieza se queda en su
    // estado estático con los controles ocultos, que es legible. Ponerla antes
    // dejaría a la vista botones que no hacen nada.
    // El repo marca la raíz de cada pieza como <main class="piece" id="…">, en
    // inglés. Se acepta tal cual para que migrar una pieza no obligue a tocar
    // su etiqueta principal; «pieza» y data-pieza valen igual.
    var raices = qsa(".piece, .pieza, [data-pieza]");
    if (!raices.length && document.body) raices = [document.body];
    raices.forEach(function (r) { r.classList.add("ready"); });
  }

  Piezas.arranca = arranca;
  global.Piezas = Piezas;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", arranca);
  } else {
    arranca();                            // con defer el DOM ya está
  }
})(typeof window !== "undefined" ? window : this);
