/* ============================================================
   piezas.elur.es — pieza "apple-upgrade"
   Calculadora comprar vs. alquilar. Mejora progresiva.
   El DOM ya muestra el CASO POR DEFECTO calculado (iPhone 17 Pro,
   24 meses: 767,76 $ de alquiler vs 1.099 $ de compra).
   Sin JS (o si esto falla) la pieza se lee entera igual.
   ============================================================ */
(function () {
  "use strict";
  var root = document.getElementById("apple");
  if (!root) return;

  // Precios oficiales de Apple Upgrade (EE. UU., lanzamiento 28-jul-2026).
  // Verificados en apple.com/shop/apple-upgrade y fichas de producto:
  // iPhone 17 Pro 256GB, Apple Watch Series 11 42mm, iPad Pro 256GB y
  // MacBook Pro 14" 16GB coinciden exactamente con las cuotas oficiales
  // publicadas por Apple. El resto procede de la Ficha G1 (Apple
  // Newsroom, MacRumors, AppleInsider, 28-jul-2026) — Apple no muestra
  // la cuota de cada configuración fuera de esos ejemplos destacados.
  var DEVICES = [
    { id: "iphone17e", name: "iPhone 17e 256GB", category: "iPhone", retail: 599, leases: { 24: 17.99 } },
    { id: "iphoneAir", name: "iPhone Air 256GB", category: "iPhone", retail: 999, leases: { 12: 41.99, 24: 28.99 } },
    { id: "iphone17pro", name: "iPhone 17 Pro 256GB", category: "iPhone", retail: 1099, leases: { 12: 45.99, 24: 31.99 } },
    { id: "watch11", name: "Apple Watch Series 11 42mm", category: "Watch", retail: 399, leases: { 12: 21.99, 24: 11.99 } },
    { id: "watchUltra3", name: "Apple Watch Ultra 3", category: "Watch", retail: 799, leases: { 12: 44.99, 24: 24.99 } },
    { id: "ipadMini", name: "iPad mini 128GB", category: "iPad", retail: 499, leases: { 24: 15.99, 36: 11.99 } },
    { id: "ipadAir", name: "iPad Air 11\" 128GB", category: "iPad", retail: 599, leases: { 24: 19.99, 36: 15.99 } },
    { id: "ipadPro", name: "iPad Pro 256GB", category: "iPad", retail: 1199, leases: { 24: 31.99, 36: 24.99 } },
    { id: "mba13", name: "MacBook Air 13\"", category: "Mac", retail: 1299, leases: { 24: 34.99, 36: 24.99 } },
    { id: "mba15", name: "MacBook Air 15\"", category: "Mac", retail: 1499, leases: { 36: 28.99 } },
    { id: "mbp14", name: "MacBook Pro 14\" 16GB", category: "Mac", retail: 1999, leases: { 24: 53.99, 36: 38.99 } }
  ];
  var CATEGORIES = ["iPhone", "Watch", "iPad", "Mac"];
  var HORIZONS = [2, 4, 6];
  // Apple Card Monthly Installments no tiene el plazo del alquiler: lo
  // fija Apple por categoría (support.apple.com/en-us/102730, consultado
  // el 2-sep-2026): 24 meses en iPhone; 12 en iPad, Apple Watch y Mac.
  // Antes esta cuota se dividía entre el plazo del arrendamiento y salían
  // plazos de ACMI que no existen (36 meses en Mac, 24 en iPad).
  var ACMI_TERMS = { iPhone: 24, Watch: 12, iPad: 12, Mac: 12 };

  // La calculadora escribe su veredicto entero desde JS, así que sin esta
  // tabla la página inglesa mostraría un párrafo en castellano. El idioma
  // se decide como en formato.js: por el lang del documento.
  var EN = /^en/i.test(document.documentElement.getAttribute("lang") || "");

  function meses(n) { return n + (EN ? " months" : " meses"); }
  function anios(n) { return EN ? n + (n === 1 ? " year" : " years")
                                : n + (n === 1 ? " año" : " años"); }

  function money(n, decimals) {
    // Fuente única: assets/formato.js. Antes esto era un formateador a mano
    // porque el ICU de algunos navegadores no separa millares en es-ES.
    if (window.Formato) return window.Formato.moneda(n, decimals, "$");
    // Reserva sin formato.js. El símbolo cambia de sitio con el idioma:
    // 1.099 $ en español, $1,099 en inglés.
    var dec = decimals == null ? (Number.isInteger(n) ? 0 : 2) : decimals;
    var parts = n.toFixed(dec).split(".");
    var intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, EN ? "," : ".");
    var txt = dec > 0 ? intPart + (EN ? "." : ",") + parts[1] : intPart;
    return EN ? "$" + txt : txt + " $";
  }

  function buildChartPaths(monthly, retail, horizonMonths) {
    var W = 320, H = 140, PAD = 8;
    var maxY = Math.max(monthly * horizonMonths, retail) * 1.05;
    var steps = 24;
    var pts = [];
    for (var i = 0; i <= steps; i++) {
      var m = (horizonMonths / steps) * i;
      var x = PAD + (W - 2 * PAD) * (m / horizonMonths);
      var yRent = H - PAD - (H - 2 * PAD) * ((monthly * m) / maxY);
      pts.push([x, yRent]);
    }
    var rentPath = pts.map(function (p, i) {
      return (i === 0 ? "M" : "L") + p[0].toFixed(1) + "," + p[1].toFixed(1);
    }).join(" ");
    var buyY = H - PAD - (H - 2 * PAD) * (retail / maxY);
    var buyPath = "M" + PAD + "," + buyY.toFixed(1) + " L" + (W - PAD) + "," + buyY.toFixed(1);
    return { rentPath: rentPath, buyPath: buyPath };
  }

  function run() {
    try { init(); root.classList.add("ready"); }
    catch (e) { /* degrada al caso por defecto ya presente en el DOM */ }
  }

  function init() {
    var controls = document.getElementById("calc-controls");
    var catWrap = document.getElementById("calc-cat");
    var devWrap = document.getElementById("calc-dev");
    var termWrap = document.getElementById("calc-term");
    var horWrap = document.getElementById("calc-horizon");
    var radioProfesional = document.getElementById("calc-use-profesional");
    var radioCapricho = document.getElementById("calc-use-capricho");
    if (!controls || !catWrap || !devWrap || !termWrap || !horWrap) return;

    var out = {
      monthly: document.getElementById("calc-monthly"),
      retail: document.getElementById("calc-retail"),
      termLabel1: document.getElementById("calc-term-label"),
      termLabel2: document.getElementById("calc-term-label-2"),
      horizonLabel1: document.getElementById("calc-horizon-label"),
      horizonLabel2: document.getElementById("calc-horizon-label-2"),
      totalRent: document.getElementById("calc-total-rent"),
      totalBuy: document.getElementById("calc-total-buy"),
      barFill: document.getElementById("calc-bar-fill"),
      pctLabel: document.getElementById("calc-pct-label"),
      finance: document.getElementById("calc-finance"),
      verdict: document.getElementById("calc-verdict"),
      chartRent: document.getElementById("calc-chart-rent"),
      chartBuy: document.getElementById("calc-chart-buy")
    };

    var state = { category: "iPhone", deviceId: "iphone17pro", term: 24, horizon: 2, useCase: "capricho" };

    function deviceById(id) { return DEVICES.filter(function (d) { return d.id === id; })[0]; }
    function inCategory(cat) { return DEVICES.filter(function (d) { return d.category === cat; }); }
    function terms(device) {
      return Object.keys(device.leases).map(Number).sort(function (a, b) { return a - b; });
    }

    function renderTabs(wrap, items, isSelected, onSelect, labelFn) {
      wrap.innerHTML = "";
      items.forEach(function (item) {
        var b = document.createElement("button");
        b.type = "button";
        b.textContent = labelFn(item);
        var sel = isSelected(item);
        b.setAttribute("aria-pressed", sel ? "true" : "false");
        b.addEventListener("click", function () { onSelect(item); render(); });
        wrap.appendChild(b);
      });
    }

    function renderDevices(device) {
      devWrap.innerHTML = "";
      inCategory(state.category).forEach(function (d) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "calc-dev-card";
        var sel = d.id === device.id;
        b.setAttribute("aria-pressed", sel ? "true" : "false");
        b.innerHTML = '<span class="calc-dev-name"></span><span class="calc-dev-price"></span>';
        b.querySelector(".calc-dev-name").textContent = d.name;
        b.querySelector(".calc-dev-price").textContent = money(d.retail) + (EN ? " outright" : " al contado");
        b.addEventListener("click", function () {
          state.deviceId = d.id;
          state.term = terms(d)[0];
          render();
        });
        devWrap.appendChild(b);
      });
    }

    function render() {
      var device = deviceById(state.deviceId) || inCategory(state.category)[0];
      var tOptions = terms(device);
      if (tOptions.indexOf(state.term) === -1) state.term = tOptions[0];
      var horizon = HORIZONS.indexOf(state.horizon) !== -1 ? state.horizon : 2;

      renderTabs(catWrap, CATEGORIES, function (c) { return c === state.category; }, function (c) {
        state.category = c;
        var first = inCategory(c)[0];
        state.deviceId = first.id;
        state.term = terms(first)[0];
      }, function (c) { return c; });

      renderDevices(device);

      renderTabs(termWrap, tOptions, function (t) { return t === state.term; }, function (t) {
        state.term = t;
      }, meses);

      renderTabs(horWrap, HORIZONS, function (h) { return h === state.horizon; }, function (h) {
        state.horizon = h;
      }, anios);

      var monthly = device.leases[state.term];
      var totalLease = Math.round(monthly * state.term * 100) / 100;
      var buyout = Math.round((device.retail - totalLease) * 100) / 100;
      var pct = Math.min(100, (totalLease / device.retail) * 100);
      var acmiTerm = ACMI_TERMS[device.category] || state.term;
      var financeMonthly = Math.round((device.retail / acmiTerm) * 100) / 100;
      var horizonMonths = horizon * 12;
      var totalRentHorizon = Math.round(monthly * horizonMonths * 100) / 100;
      var isProfesional = state.useCase === "profesional";

      if (radioProfesional) radioProfesional.checked = isProfesional;
      if (radioCapricho) radioCapricho.checked = !isProfesional;

      if (out.monthly) out.monthly.textContent = money(monthly) + (EN ? " /mo" : " /mes");
      if (out.retail) out.retail.textContent = money(device.retail);
      var termTxt = meses(state.term), horTxt = anios(horizon);
      if (out.termLabel1) out.termLabel1.textContent = termTxt;
      if (out.termLabel2) out.termLabel2.textContent = termTxt;
      if (out.horizonLabel1) out.horizonLabel1.textContent = horTxt;
      if (out.horizonLabel2) out.horizonLabel2.textContent = horTxt;
      if (out.totalRent) out.totalRent.textContent = money(totalRentHorizon);
      if (out.totalBuy) out.totalBuy.textContent = money(device.retail);
      if (out.barFill) out.barFill.style.width = pct.toFixed(0) + "%";
      if (out.pctLabel) out.pctLabel.textContent = pct.toFixed(0) +
      (EN ? "% of the device's value \u00b7 buyout: " : "% del valor del aparato \u00b7 recompra: ") + money(buyout);
      if (out.finance) out.finance.textContent = EN
      ? money(financeMonthly) + " /mo over " + acmiTerm + " months \u2014 by instalments you end up the owner, at no extra cost thanks to the 0% interest."
      : money(financeMonthly) + " /mes a " + acmiTerm + " meses \u2014 a plazo terminas siendo due\u00f1o, sin coste extra por el 0% de inter\u00e9s.";

      if (out.chartRent && out.chartBuy) {
        var paths = buildChartPaths(monthly, device.retail, horizonMonths);
        out.chartRent.setAttribute("d", paths.rentPath);
        out.chartBuy.setAttribute("d", paths.buyPath);
      }

      if (out.verdict) {
        var verdictText;
        if (isProfesional) {
          verdictText = EN
            ? "If it is work kit: paying " + money(monthly) + "/mo frees up " + money(device.retail) +
              " of cash today. With the buyout this calculation assumes (" + money(totalLease) + " + " + money(buyout) +
              " = " + money(device.retail) + "), keeping it at the end of the first cycle costs the same as buying it outright or financing it at 0% with Apple Card, which is sold in the United States only (" +
              money(financeMonthly) + "/mo over " + acmiTerm + " months). It is worth it if the margin from not tying up that money beats what you risk by depending on Klarna and its terms."
            : "Si es material de trabajo: pagando " + money(monthly) + "/mes liberas " + money(device.retail) +
              " de caja hoy. Con la recompra que asume este c\u00e1lculo (" + money(totalLease) + " + " + money(buyout) +
              " = " + money(device.retail) + "), qued\u00e1rtelo al final del primer ciclo cuesta lo mismo que comprarlo de una vez o financiarlo a 0% con Apple Card (" +
              money(financeMonthly) + "/mes a " + acmiTerm + " meses). Compensa si el margen de no inmovilizar ese dinero supera lo que arriesgas por depender de Klarna y sus condiciones.";
        } else {
          // El veredicto dice lo que dice el cálculo, no lo contrario. En el
          // horizonte por defecto (2 años) el alquiler sale MÁS BARATO en caja
          // que la compra, y durante meses la pieza concluía justo lo opuesto.
          // La diferencia cambia de signo según el horizonte, así que se calcula.
          var diffH = Math.round((device.retail - totalRentHorizon) * 100) / 100;
          var cmp;
          if (EN) {
            if (diffH > 0) cmp = "Over that horizon renting comes out " + money(diffH) + " cheaper in cash, but you are left with no device.";
            else if (diffH < 0) cmp = "Over that horizon renting comes out " + money(-diffH) + " dearer, and you are left with no device on top of that.";
            else cmp = "Over that horizon renting costs the same, and you are left with no device on top of that.";
            verdictText = "If it is a treat: renewing every " + meses(state.term) + ", in " + horTxt + " you will have paid " +
              money(totalRentHorizon) + " without the device ever becoming yours at any point, against " + money(device.retail) +
              " paid once if you buy it and keep it. " + cmp +
              " The calculation credits the bought device with no resale value: the more it is worth second-hand, the worse renting looks.";
          } else {
          if (diffH > 0) cmp = "En ese horizonte el alquiler sale " + money(diffH) + " m\u00e1s barato en caja, pero te quedas sin aparato.";
          else if (diffH < 0) cmp = "En ese horizonte el alquiler sale " + money(-diffH) + " m\u00e1s caro, y adem\u00e1s te quedas sin aparato.";
          else cmp = "En ese horizonte el alquiler cuesta lo mismo, y adem\u00e1s te quedas sin aparato.";
          verdictText = "Si es un capricho: renovando cada " + state.term + " meses, en " + horTxt + " habr\u00e1s pagado " +
            money(totalRentHorizon) + " sin que el aparato llegue a ser tuyo en ning\u00fan momento, frente a " + money(device.retail) +
            " pagados una sola vez si lo compras y lo conservas. " + cmp +
            " El c\u00e1lculo no le asigna valor de reventa al comprado: cuanto m\u00e1s valga de segunda mano, peor sale el alquiler.";
          }
        }
        out.verdict.textContent = verdictText;
      }
    }

    if (radioProfesional) radioProfesional.addEventListener("change", function () { state.useCase = "profesional"; render(); });
    if (radioCapricho) radioCapricho.addEventListener("change", function () { state.useCase = "capricho"; render(); });

    controls.hidden = false;
    render();
  }

  run();
})();
