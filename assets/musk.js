/* ============================================================
   piezas.elur.es — pieza "musk-ceguera"
   Mejoras progresivas de los 4 interactivos.
   Principio del repo: el DOM ya muestra el ESTADO FINAL.
   Sin JS (o si esto falla) la pieza se lee entera igual.
   ============================================================ */
(function () {
  "use strict";
  var musk = document.getElementById("musk");
  if (!musk) return;

  // ---- Escena compartida G2 (misma función de luminancia que el generador) ----
  function lum(x, y) {
    var base = 0.10; // muro
    if (x >= 0.30 && x <= 0.70 && y >= 0.08) {
      base = 0.92; // portal iluminado
      var dx = x - 0.50, dy = y - 0.32;
      if ((dx * dx) / (0.075 * 0.075) + (dy * dy) / (0.09 * 0.09) <= 1) base = 0.06; // cabeza
      if (y >= 0.42 && y <= 0.92) {
        var half = 0.085 + (y - 0.42) * 0.10;
        if (Math.abs(x - 0.50) <= half) base = 0.06; // cuerpo
      }
    }
    return base;
  }

  function run() {
    safe(initPromesa);
    safe(initFosfenos);
    safe(initMapa);
    safe(initVia3D);
    musk.classList.add("ready");
  }
  function safe(fn) { try { fn(); } catch (e) { /* degrada al estado estático */ } }

  // ========================================================
  // G1 — Timeline promesa vs realidad
  // ========================================================
  function initPromesa() {
    var tl = document.getElementById("promesa-tl");
    var readout = document.getElementById("promesa-readout");
    if (!tl || !readout) return;
    var items = Array.prototype.slice.call(tl.querySelectorAll(".tl-item"));
    var TODAY = new Date(2026, 7, 11); // 11 ago 2026
    var M = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"];
    function fmt(d){ return d.getDate() + " " + M[d.getMonth()] + " " + d.getFullYear(); }
    function select(item) {
      items.forEach(function (x) { x.classList.remove("sel"); x.setAttribute("aria-pressed", "false"); });
      item.classList.add("sel"); item.setAttribute("aria-pressed", "true");
      var p = item.getAttribute("data-date").split("-");
      var d = new Date(+p[0], +p[1] - 1, +p[2]);
      var days = Math.round((TODAY - d) / 86400000);
      readout.innerHTML = "Prometido el <b>" + fmt(d) + "</b>. Hoy, <b>" + days +
        " días</b> después: Blindsight sigue en <b>0 pacientes</b>, 0 estudios revisados y 0 registros.";
    }
    items.forEach(function (it) {
      it.addEventListener("click", function () { select(it); });
      it.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(it); }
      });
    });
    select(items[items.length - 1]); // arranca en la última promesa
  }

  // ========================================================
  // G2 — Simulador de fosfenos (canvas)
  // ========================================================
  function initFosfenos() {
    var stage = document.getElementById("phos-stage");
    var range = document.getElementById("phos-range");
    var elec = document.getElementById("phos-elec");
    if (!stage || !range || !elec) return;

    var W = 640, H = 480;
    var canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    canvas.className = "phos-canvas";
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label",
      "Escena real (una persona en un portal iluminado) que se revela como una rejilla de fosfenos según el número de electrodos.");
    var ctx = canvas.getContext("2d");
    if (!ctx) return; // sin canvas: se queda el SVG estático

    var svg = stage.querySelector(".phos-static");
    if (svg) svg.style.display = "none";
    stage.insertBefore(canvas, stage.firstChild);

    var GRID = { 60: [9, 7], 200: [16, 13], 1000: [36, 28] };
    var state = { reveal: +range.value || 50, e: 60 };

    function drawScene() {
      ctx.fillStyle = "#100D09"; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = "#F4EFE4"; ctx.fillRect(0.30 * W, 0.08 * H, 0.40 * W, 0.92 * H);
      ctx.fillStyle = "#100D09";
      ctx.beginPath();
      ctx.ellipse(0.50 * W, 0.32 * H, 0.075 * W, 0.09 * H, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo((0.50 - 0.085) * W, 0.42 * H);
      ctx.lineTo((0.50 + 0.085) * W, 0.42 * H);
      ctx.lineTo((0.50 + 0.135) * W, 0.92 * H);
      ctx.lineTo((0.50 - 0.135) * W, 0.92 * H);
      ctx.closePath(); ctx.fill();
    }
    function label(txt, x, y, anchorRight) {
      ctx.font = "600 15px ui-monospace, Menlo, monospace";
      var w = ctx.measureText(txt).width + 12;
      ctx.fillStyle = "rgba(16,13,9,0.55)";
      ctx.fillRect(anchorRight ? x - w : x, y, w, 22);
      ctx.fillStyle = "#F4EFE4";
      ctx.fillText(txt, (anchorRight ? x - w : x) + 6, y + 15);
    }
    function render() {
      drawScene();
      var divX = W * state.reveal / 100;
      ctx.save();
      ctx.beginPath(); ctx.rect(divX, 0, W - divX, H); ctx.clip();
      ctx.fillStyle = "#100D09"; ctx.fillRect(divX, 0, W - divX, H);
      var g = GRID[state.e], cols = g[0], rows = g[1];
      var cw = W / cols, ch = H / rows, maxr = Math.min(cw, ch) * 0.46;
      ctx.fillStyle = "#F4EFE4";
      for (var j = 0; j < rows; j++) {
        for (var i = 0; i < cols; i++) {
          var cx = (i + 0.5) * cw, cy = (j + 0.5) * ch;
          var L = lum(cx / W, cy / H);
          var r = maxr * Math.sqrt(L);
          ctx.globalAlpha = 0.12 + 0.88 * L;
          ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
      ctx.restore();
      // divisor
      ctx.fillStyle = "#F4EFE4"; ctx.globalAlpha = 0.7;
      ctx.fillRect(divX - 1, 0, 2, H); ctx.globalAlpha = 1;
      // etiquetas
      label("VISIÓN NORMAL", 8, 8, false);
      label("SIMULACIÓN · " + fmtNum(state.e) + " ELECTRODOS", W - 8, 8, true);
    }
    function fmtNum(n) { return n >= 1000 ? "1.000" : String(n); }

    range.addEventListener("input", function () { state.reveal = +range.value; render(); });
    Array.prototype.slice.call(elec.querySelectorAll("button")).forEach(function (b) {
      b.addEventListener("click", function () {
        state.e = +b.getAttribute("data-e");
        Array.prototype.slice.call(elec.querySelectorAll("button")).forEach(function (x) {
          x.setAttribute("aria-pressed", x === b ? "true" : "false");
        });
        render();
      });
    });
    render();
  }

  // ========================================================
  // G3 — Mapa: filtro por fase
  // ========================================================
  function initMapa() {
    var filters = document.getElementById("map-filters");
    var fig = document.getElementById("fig-mapa");
    if (!filters || !fig) return;
    var marks = Array.prototype.slice.call(fig.querySelectorAll(".map-static .mk"));
    var rows = Array.prototype.slice.call(fig.querySelectorAll(".mrow"));
    var groups = Array.prototype.slice.call(fig.querySelectorAll(".phase-group"));
    var btns = Array.prototype.slice.call(filters.querySelectorAll("button"));

    function apply(f) {
      marks.forEach(function (m) {
        m.classList.toggle("dim", !(f === "all" || m.getAttribute("data-fase") === f));
      });
      rows.forEach(function (r) {
        r.classList.toggle("dim", !(f === "all" || r.getAttribute("data-fase") === f));
      });
      groups.forEach(function (g) {
        g.style.display = g.querySelectorAll(".mrow:not(.dim)").length ? "" : "none";
      });
      btns.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-f") === f ? "true" : "false");
      });
    }
    btns.forEach(function (b) {
      b.addEventListener("click", function () { apply(b.getAttribute("data-f")); });
    });
    apply("all");
  }

  // ========================================================
  // G4 — Explorador 3D de la vía visual (three.js self-hosted)
  // ========================================================
  function initVia3D() {
    var btn = document.getElementById("via-3d-btn");
    var box = document.getElementById("via-3d");
    var canvas = document.getElementById("via-canvas");
    if (!btn || !box || !canvas) return;
    var started = false, visible = false, anim = null, THREEref = null, sceneApi = null;

    btn.addEventListener("click", function () {
      if (!started) {
        btn.disabled = true;
        btn.textContent = "Cargando 3D…";
        loadThree(function (ok) {
          btn.disabled = false;
          if (!ok || !window.THREE) {
            box.hidden = false;
            box.innerHTML = '<p class="hint">No se pudo cargar el visor 3D. La ilustración de arriba muestra el recorrido completo.</p>';
            btn.style.display = "none";
            return;
          }
          THREEref = window.THREE;
          box.hidden = false;
          try { sceneApi = buildScene(THREEref, canvas); }
          catch (e) {
            box.innerHTML = '<p class="hint">Tu dispositivo no admite el visor 3D. La ilustración de arriba muestra el recorrido completo.</p>';
            btn.style.display = "none";
            return;
          }
          started = true; visible = true;
          btn.textContent = "Ocultar 3D";
          btn.setAttribute("aria-expanded", "true");
        });
      } else {
        visible = !visible;
        box.hidden = !visible;
        btn.textContent = visible ? "Ocultar 3D" : "Explorar en 3D ▸";
        btn.setAttribute("aria-expanded", visible ? "true" : "false");
        if (visible && sceneApi) sceneApi.resume();
      }
    });

    function loadThree(cb) {
      if (window.THREE) return cb(true);
      var s = document.createElement("script");
      s.src = "../assets/three.min.js";
      s.async = true;
      s.onload = function () { cb(true); };
      s.onerror = function () { cb(false); };
      document.head.appendChild(s);
    }

    function buildScene(THREE, canvas) {
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(640, 320, false); // buffer lógico 640×320 (×pixelRatio); CSS lo escala

      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(42, 2, 0.1, 100);
      camera.position.set(0, 0.5, 7.2);
      camera.lookAt(0, 0, 0);

      scene.add(new THREE.AmbientLight(0xffffff, 0.8));
      var dir = new THREE.DirectionalLight(0xffffff, 0.7);
      dir.position.set(3, 5, 4); scene.add(dir);

      var group = new THREE.Group(); scene.add(group);

      // ojo
      var eye = new THREE.Mesh(
        new THREE.SphereGeometry(0.72, 40, 28),
        new THREE.MeshStandardMaterial({ color: 0xF4EFE4, roughness: 0.65 }));
      eye.position.set(-2.7, 0, 0); group.add(eye);
      var iris = new THREE.Mesh(
        new THREE.SphereGeometry(0.26, 24, 18),
        new THREE.MeshStandardMaterial({ color: 0x3F5A63, roughness: 0.5 }));
      iris.position.set(-3.36, 0, 0); group.add(iris);

      // nervio óptico (tubo por una curva)
      var curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(-2.1, 0, 0),
        new THREE.Vector3(-0.7, -0.5, 0.15),
        new THREE.Vector3(0.9, -0.4, -0.1),
        new THREE.Vector3(2.1, 0.15, 0)
      ]);
      var nerve = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 80, 0.14, 14, false),
        new THREE.MeshStandardMaterial({ color: 0x797064, roughness: 0.8 }));
      group.add(nerve);

      // corteza visual
      var cortex = new THREE.Mesh(
        new THREE.SphereGeometry(1.15, 40, 28),
        new THREE.MeshStandardMaterial({ color: 0xB84A2C, roughness: 0.55 }));
      cortex.position.set(2.8, 0.15, 0); cortex.scale.set(1, 0.86, 0.92);
      group.add(cortex);

      // marcadores (retina / corteza)
      var mkRet = new THREE.Mesh(
        new THREE.SphereGeometry(0.16, 20, 16),
        new THREE.MeshStandardMaterial({ color: 0x3F5A63, emissive: 0x3F5A63, emissiveIntensity: 0.6 }));
      mkRet.position.set(-2.15, 0.05, 0.55); group.add(mkRet);
      var mkCtx = new THREE.Mesh(
        new THREE.SphereGeometry(0.18, 20, 16),
        new THREE.MeshStandardMaterial({ color: 0xB84A2C, emissive: 0xB84A2C, emissiveIntensity: 0.75 }));
      mkCtx.position.set(2.15, 0.35, 0.8); group.add(mkCtx);

      group.rotation.y = -0.35;

      // interacción: arrastrar para girar
      var dragging = false, lx = 0, ly = 0, running = true;
      function down(e){ dragging = true; var p = pt(e); lx = p.x; ly = p.y; }
      function move(e){
        if (!dragging) return;
        var p = pt(e);
        group.rotation.y += (p.x - lx) * 0.01;
        group.rotation.x += (p.y - ly) * 0.01;
        group.rotation.x = Math.max(-0.9, Math.min(0.9, group.rotation.x));
        lx = p.x; ly = p.y;
        if (e.cancelable) e.preventDefault();
      }
      function up(){ dragging = false; }
      function pt(e){ var t = e.touches ? e.touches[0] : e; return { x: t.clientX, y: t.clientY }; }
      canvas.addEventListener("pointerdown", down);
      window.addEventListener("pointermove", move, { passive: false });
      window.addEventListener("pointerup", up);

      function loop() {
        anim = requestAnimationFrame(loop);
        if (!dragging && !reduce) group.rotation.y += 0.004;
        renderer.render(scene, camera);
      }
      loop();

      return {
        resume: function () { if (!anim) loop(); },
        stop: function () { if (anim) { cancelAnimationFrame(anim); anim = null; } }
      };
    }
  }

  // arranque (defer garantiza DOM listo)
  run();
})();
