/* ============================================================
   piezas.elur.es — pieza "cafe-salud"
   Taza interactiva «Llena tu café». Mejora progresiva. SIN PUNTUACIÓN:
   ver el bloque de NOTAS más abajo, que explica por qué se retiró.
   El DOM ya muestra el CASO POR DEFECTO (café solo, tamaño normal).
   Sin JS (o si esto falla) la pieza se lee entera igual; los controles
   solo aparecen con JS.
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
    var labelEl = document.getElementById("cafe-label");
    var explainEl = document.getElementById("cafe-explain");
    var cupEl = document.getElementById("cafe-cup");
    var layerCoffee = document.getElementById("layer-coffee");
    var layerMilk = document.getElementById("layer-milk");
    var layerExtra = document.getElementById("layer-extra");
    var cupSizeEl = document.getElementById("cafe-cup-size");
    if (!controls || !labelEl || !explainEl) return;

    var buttons = Array.prototype.slice.call(controls.querySelectorAll(".cafe-tag"));
    if (!buttons.length) return;

    var state = { base: "calidad", leche: "ninguna", extras: [], tamano: "normal" };

    /* ------------------------------------------------------------------
       AQUÍ NO SE PUNTÚA, Y ES DELIBERADO.
       La versión anterior daba una nota de 0 a 100 con ocho coeficientes
       fijados a mano (cápsula −20, entera −5, vegetal −2, azúcar −20,
       sirope −25, nata −20, grande −10). No había fuente detrás de ninguno:
       ni Kim 2019 ni Ding 2014 estratifican por añadidos ni por formato, y
       Ding lo dice en sus propias limitaciones —«none of the studies
       assessed the amount of sugar and dairy added to coffee» y «Coffee
       brewing methods were not assessed in the studies»—. Una escala
       numérica le daba apariencia de medida a ocho cifras elegidas, en una
       pieza de salud. Se retira.
       Lo que queda es descriptivo: cómo se llama lo que hay en la taza y
       qué dice —o no dice— la evidencia sobre cada añadido.
       ------------------------------------------------------------------ */
    var NOTAS = {
      // Tverdal 2020 (508.747 personas) es lo único localizado sobre formato,
      // y separa filtrado de no filtrado, no cápsula de café de calidad.
      capsula: "de la cápsula no hay estudio: del formato solo se ha medido filtrado frente a no filtrado, y la cápsula es filtrada",
      // Kim 2019 mantiene la asociación «irrespective of caffeine content»;
      // Ding 2014 mide el descafeinado y no halla diferencia (P = 0,17).
      descaf: "el descafeinado no resta: las dos fuentes de esta pieza lo miden y no encuentran diferencia significativa",
      entera: "la leche que se echa al café no se ha medido en ninguno de estos estudios",
      vegetal: "la leche vegetal tampoco se ha medido",
      // Zhou 2025 frente a Liu 2022: la única discrepancia documentada.
      azucar: "el azúcar es lo único añadido con estudios, y no coinciden: Zhou 2025 solo encuentra el beneficio en café solo o con poco azúcar, y Liu 2022 lo encuentra también con azúcar en dosis moderada",
      sirope: "del sirope no hay ningún estudio que lo mida",
      nata: "la nata no se ha medido por separado; lo medido es la grasa saturada añadida",
      grande: "los estudios cuentan tazas al día, no el tamaño de la taza"
    };

    function lectura() {
      var notas = [];
      if (NOTAS[state.base]) notas.push(NOTAS[state.base]);
      if (NOTAS[state.leche]) notas.push(NOTAS[state.leche]);
      ["azucar", "sirope", "nata"].forEach(function (e) {
        if (state.extras.indexOf(e) !== -1) notas.push(NOTAS[e]);
      });
      if (state.tamano === "grande") notas.push(NOTAS.grande);

      // Etiqueta descriptiva: nombra lo que hay en la taza. No ordena nada.
      var etiqueta = "Café solo";
      if (state.leche !== "ninguna") etiqueta = "Café con leche";
      if (state.extras.length) etiqueta = "Café con azúcar o grasa añadida";

      var explicacion = "Café solo, sin azúcar ni grasa añadida: así es como se mide el beneficio en los estudios.";
      if (notas.length) {
        var t = notas.join("; ") + ".";
        explicacion = t.charAt(0).toUpperCase() + t.slice(1);
      }

      return { etiqueta: etiqueta, explicacion: explicacion };
    }

    function render() {
      var r = lectura();
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
