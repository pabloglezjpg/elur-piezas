/* ============================================================
   piezas.elur.es — pieza "tim-cook-apple"
   Selector de métrica (Ingresos / Beneficio neto / Capitalización).
   El DOM ya muestra el caso por defecto (Ingresos, serie completa).
   Sin JS (o si esto falla) la pieza se lee entera igual.
   ============================================================ */
(function () {
  "use strict";
  var root = document.getElementById("tcook");
  if (!root) return;

  // SVG elements don't reflect the HTML `hidden` IDL property to the
  // attribute (that property lives on HTMLElement, not SVGElement), so
  // toggling .hidden silently no-ops on the chart <svg> panels. Use the
  // attribute directly — it works on any element and is what the
  // `[hidden]` CSS in the page's <style> actually matches on.
  function setHidden(el, isHidden) {
    if (isHidden) el.setAttribute("hidden", "");
    else el.removeAttribute("hidden");
  }

  function init() {
    var tabs = document.getElementById("metric-tabs");
    if (!tabs) return;
    var buttons = Array.prototype.slice.call(tabs.querySelectorAll("button[data-m]"));
    var panels = Array.prototype.slice.call(document.querySelectorAll(".metric-panel"));
    var readouts = Array.prototype.slice.call(document.querySelectorAll("[data-readout]"));

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var metric = btn.getAttribute("data-m");
        buttons.forEach(function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });
        panels.forEach(function (p) {
          setHidden(p, p.getAttribute("data-metric") !== metric);
        });
        readouts.forEach(function (r) {
          setHidden(r, r.getAttribute("data-readout") !== metric);
        });
      });
    });
  }

  try { init(); root.classList.add("ready"); } catch (e) { /* la pieza ya se lee bien sin esto */ }
})();
