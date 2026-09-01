/* ============================================================
   piezas.elur.es — pieza "cafe-salud"
   Minijuego «Llena tu café». Mejora progresiva.
   El DOM ya muestra el CASO POR DEFECTO (café de calidad, solo,
   tamaño normal: puntuación 100). Sin JS (o si esto falla) la
   pieza se lee entera igual; los controles solo aparecen con JS.
   ============================================================ */
(function () {
  "use strict";
  var piece = document.getElementById("cafe");
  if (!piece) return;

  function run() {
    safe(initJuego);
    piece.classList.add("ready");
  }
  function safe(fn) { try { fn(); } catch (e) { /* degrada al estado estático */ } }

  function initJuego() {
    var controls = document.getElementById("cafe-controls");
    var scoreEl = document.getElementById("cafe-score");
    var labelEl = document.getElementById("cafe-label");
    var explainEl = document.getElementById("cafe-explain");
    var cupEl = document.getElementById("cafe-cup");
    var layerCoffee = document.getElementById("layer-coffee");
    var layerMilk = document.getElementById("layer-milk");
    var layerExtra = document.getElementById("layer-extra");
    var cupSizeEl = document.getElementById("cafe-cup-size");
    if (!controls || !scoreEl || !labelEl || !explainEl) return;

    var buttons = Array.prototype.slice.call(controls.querySelectorAll(".cafe-tag"));
    if (!buttons.length) return;

    var state = { base: "calidad", leche: "ninguna", extras: [], tamano: "normal" };

    function score() {
      var s = 100;
      var notas = [];
      if (state.base === "capsula") { s -= 20; notas.push("la cápsula barata resta frente a un café de calidad"); }
      // Sin penalización: Kim 2019 mantiene la asociación «irrespective of caffeine content»
      // y Ding 2014 mide el descafeinado y no encuentra diferencia significativa (P = 0,17).
      if (state.base === "descaf") { notas.push("el descafeinado no resta: las dos fuentes de esta pieza lo miden y no encuentran diferencia significativa"); }
      if (state.leche === "entera") s -= 5;
      if (state.leche === "vegetal") s -= 2;
      if (state.extras.indexOf("azucar") !== -1) { s -= 20; notas.push("el azúcar te aleja del café tal cual se estudió"); }
      if (state.extras.indexOf("sirope") !== -1) { s -= 25; notas.push("el sirope convierte la taza en un postre líquido"); }
      if (state.extras.indexOf("nata") !== -1) { s -= 20; notas.push("la nata suma calorías que no forman parte del beneficio"); }
      if (state.tamano === "grande") { s -= 10; notas.push("el tamaño grande multiplica cualquier añadido"); }
      s = Math.max(0, Math.min(100, s));

      var etiqueta = "Café tal cual se estudió";
      if (s < 90 && s >= 65) etiqueta = "Se aleja un poco";
      if (s < 65 && s >= 35) etiqueta = "Ya es otra cosa";
      if (s < 35) etiqueta = "Postre líquido";

      var explicacion = notas.length
        ? notas.join("; ") + "."
        : "Así es como se mide el beneficio en los estudios: café, sin extras.";

      return { s: s, etiqueta: etiqueta, explicacion: explicacion };
    }

    function render() {
      var r = score();
      scoreEl.textContent = r.s;
      labelEl.textContent = r.etiqueta;
      explainEl.textContent = r.explicacion;
      renderCup();
    }

    function renderCup() {
      if (!cupEl || !layerCoffee || !layerMilk || !layerExtra) return;

      var hasMilk = state.leche !== "ninguna";
      var extraCount = state.extras.length;

      var milkH = hasMilk ? 26 : 0;
      var extraH = extraCount ? Math.min(30, extraCount * 12) : 0;
      var coffeeH = Math.max(20, 100 - milkH - extraH);

      layerCoffee.style.height = coffeeH + "%";
      layerMilk.style.height = milkH + "%";
      layerExtra.style.height = extraH + "%";

      layerCoffee.classList.toggle("capsula", state.base === "capsula");
      layerCoffee.classList.toggle("descaf", state.base === "descaf");
      layerMilk.classList.toggle("vegetal", state.leche === "vegetal");

      cupEl.classList.toggle("cafe-cup--grande", state.tamano === "grande");
      if (cupSizeEl) cupSizeEl.textContent = state.tamano === "grande" ? "Grande" : "Normal";
    }

    function selectSingle(group, value) {
      state[group] = value;
      buttons.forEach(function (b) {
        if (b.getAttribute("data-group") === group) {
          b.setAttribute("aria-pressed", b.getAttribute("data-value") === value ? "true" : "false");
        }
      });
    }

    function toggleExtra(btn, value) {
      var i = state.extras.indexOf(value);
      if (i === -1) { state.extras.push(value); btn.setAttribute("aria-pressed", "true"); }
      else { state.extras.splice(i, 1); btn.setAttribute("aria-pressed", "false"); }
    }

    buttons.forEach(function (btn) {
      var group = btn.getAttribute("data-group");
      var value = btn.getAttribute("data-value");
      btn.addEventListener("click", function () {
        if (group === "extra") toggleExtra(btn, value);
        else selectSingle(group, value);
        render();
      });
    });
  }

  // arranque (defer garantiza DOM listo)
  run();
})();
