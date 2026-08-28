/* ============================================================
   piezas.elur.es — pieza "argentina-milei"
   Mejora progresiva del dashboard de indicadores.
   Principio del repo: el DOM ya muestra el ESTADO FINAL
   (la métrica por defecto). Sin JS (o si esto falla) la pieza
   se lee entera igual; el selector solo aparece con JS.
   ============================================================ */
(function () {
  "use strict";
  var piece = document.getElementById("milei");
  if (!piece) return;

  function run() {
    safe(initDash);
    piece.classList.add("ready");
  }
  function safe(fn) { try { fn(); } catch (e) { /* degrada al estado estático */ } }

  function initDash() {
    var dash = document.getElementById("milei-dash");
    if (!dash) return;
    var tags = Array.prototype.slice.call(dash.querySelectorAll(".dash-tag"));
    var panels = Array.prototype.slice.call(dash.querySelectorAll("[data-metric-panel]"));
    if (!tags.length || !panels.length) return;

    function select(metric) {
      panels.forEach(function (p) {
        p.hidden = p.getAttribute("data-metric-panel") !== metric;
      });
      tags.forEach(function (t) {
        t.setAttribute("aria-pressed", t.getAttribute("data-metric") === metric ? "true" : "false");
      });
    }

    tags.forEach(function (t) {
      t.addEventListener("click", function () { select(t.getAttribute("data-metric")); });
    });
  }

  // arranque (defer garantiza DOM listo)
  run();
})();
