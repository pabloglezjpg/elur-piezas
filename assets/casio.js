/* ============================================================
   piezas.elur.es — pieza "casio-encogerse"
   Mejora progresiva del Gráfico 1.

   Principio del repo: sin JS la pieza se lee ENTERA. Aquí eso
   significa que los tres paneles del gráfico están visibles y
   apilados en el HTML; este script los convierte en pestañas y
   muestra los controles (.needs-js). Si falla, o si no hay JS,
   la clase .ready nunca se añade y todo sigue visible.
   ============================================================ */
(function () {
  "use strict";
  var piece = document.getElementById("casio");
  if (!piece) return;

  function safe(fn) { try { fn(); } catch (e) { /* degrada al estado estático */ } }

  function initDash() {
    var fig = document.getElementById("fig-curva");
    if (!fig) return;
    var tags = Array.prototype.slice.call(fig.querySelectorAll(".dash-tag"));
    var panels = Array.prototype.slice.call(fig.querySelectorAll("[data-metric-panel]"));
    if (!tags.length || !panels.length) return;

    function select(metric) {
      panels.forEach(function (p) {
        p.classList.toggle("is-on", p.getAttribute("data-metric-panel") === metric);
      });
      tags.forEach(function (t) {
        t.setAttribute("aria-pressed", t.getAttribute("data-metric") === metric ? "true" : "false");
      });
    }

    tags.forEach(function (t) {
      t.addEventListener("click", function () { select(t.getAttribute("data-metric")); });
    });

    // Estado inicial: el panel marcado en el HTML.
    var first = tags.filter(function (t) { return t.getAttribute("aria-pressed") === "true"; })[0] || tags[0];
    select(first.getAttribute("data-metric"));

    // Solo ahora se declara la pieza "lista": es lo que oculta los
    // paneles no elegidos y revela los controles.
    piece.classList.add("ready");
  }

  safe(initDash);
})();
