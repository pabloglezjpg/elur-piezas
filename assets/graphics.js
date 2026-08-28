/* ============================================================
   piezas.elur.es — kit de gráficas animadas
   Principio: el DOM ya muestra el ESTADO FINAL. El JS solo
   añade la animación de entrada. Sin JS → todo se ve igual.
   ============================================================ */
(function () {
  "use strict";

  // Marca <html> para activar los estados iniciales de animación
  // (solo si hay JS; así el no-JS conserva el estado final).
  var root = document.documentElement;
  root.classList.add("js");

  var reduce = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (reduce || !("IntersectionObserver" in window)) {
    // Sin animación: aseguramos estado final visible y salimos.
    finalizeAll();
    return;
  }

  // Prepara los elementos: pasan a su estado inicial "oculto/colapsado".
  prepareBars();
  prepareDraws();
  prepareReveals();

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      var el = e.target;
      if (el.hasAttribute("data-grow")) growBar(el);
      else if (el.hasAttribute("data-draw")) drawLine(el);
      else if (el.hasAttribute("data-count")) countUp(el);
      else if (el.classList.contains("reveal")) el.classList.add("in");
      io.unobserve(el);
    });
  }, { threshold: 0.25, rootMargin: "0px 0px -8% 0px" });

  qsa("[data-grow],[data-draw],[data-count],.reveal").forEach(function (el) {
    io.observe(el);
  });

  // ---- Barras ----
  function prepareBars() {
    qsa("[data-grow]").forEach(function (el) { el.classList.add("anim-bar"); });
  }
  function growBar(el) {
    // stagger según posición x para un barrido de izquierda a derecha
    var x = parseFloat(el.getAttribute("x")) || 0;
    el.style.transitionDelay = Math.min(x / 900, 0.7).toFixed(2) + "s";
    requestAnimationFrame(function () { el.classList.add("in"); });
  }

  // ---- Líneas (dibujado con dashoffset) ----
  function prepareDraws() {
    qsa("[data-draw]").forEach(function (el) {
      try {
        var len = el.getTotalLength();
        el.style.strokeDasharray = len;
        el.style.strokeDashoffset = len;
        el.classList.add("anim-draw");
        el.__len = len;
      } catch (err) { /* nodo no medible: se queda en estado final */ }
    });
  }
  function drawLine(el) {
    if (el.__len == null) return;
    // Restaura el patrón discontinuo original tras dibujar, si lo tenía.
    var dashed = el.classList.contains("uline-dash") || el.classList.contains("tl-annoline");
    requestAnimationFrame(function () {
      el.style.strokeDashoffset = "0";
      if (dashed) {
        window.setTimeout(function () {
          el.style.transition = "none";
          el.style.strokeDasharray = "6 5";
          el.style.strokeDashoffset = "0";
        }, 1550);
      }
    });
  }

  // ---- Contadores ----
  function countUp(el) {
    var target = parseFloat(el.getAttribute("data-count"));
    if (isNaN(target)) return;
    var dec = parseInt(el.getAttribute("data-decimals") || "0", 10);
    var prefix = el.getAttribute("data-prefix") || "";
    var suffix = el.getAttribute("data-suffix") || "";
    var dur = 1400, start = null, from = 0;
    function fmt(v) {
      var s = v.toLocaleString("es-ES", {
        minimumFractionDigits: dec, maximumFractionDigits: dec
      });
      return prefix + s + suffix;
    }
    function step(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(from + (target - from) * eased);
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = fmt(target);
    }
    requestAnimationFrame(step);
  }

  function prepareReveals() {
    // .reveal ya se anima vía CSS al añadir .in
  }

  // ---- Utilidades ----
  function qsa(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }

  function finalizeAll() {
    // Garantiza el estado final (por si se añadieron clases iniciales).
    qsa("[data-count]").forEach(function (el) {
      var t = parseFloat(el.getAttribute("data-count"));
      if (isNaN(t)) return;
      var dec = parseInt(el.getAttribute("data-decimals") || "0", 10);
      el.textContent = (el.getAttribute("data-prefix") || "") +
        t.toLocaleString("es-ES", { minimumFractionDigits: dec, maximumFractionDigits: dec }) +
        (el.getAttribute("data-suffix") || "");
    });
  }
})();
