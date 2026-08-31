/* ============================================================
   cultura-financiera — autotest interactivo (3 preguntas ECF)
   Sin JS el DOM muestra las TRES preguntas y las medias; con JS se van
   mostrando de una en una.
   Este script añade la interacción (preguntas 2 y 3) y el resultado.
   ============================================================ */
(function () {
  "use strict";

  var root = document.getElementById("cultfin");
  var quiz = document.getElementById("quiz");
  if (!root || !quiz) return;

  var qs = Array.prototype.slice.call(quiz.querySelectorAll(".quiz-q"));
  var output = document.getElementById("quiz-output");
  var resetBtn = document.getElementById("quiz-reset");
  var score = 0;

  root.classList.add("ready");

  function init() {
    score = 0;
    qs.forEach(function (q, i) {
      q.style.display = i === 0 ? "block" : "none";
      var opts = q.querySelectorAll(".quiz-opt");
      opts.forEach(function (b) {
        b.disabled = false;
        b.classList.remove("chosen", "is-correct", "is-wrong");
      });
    });
    if (output) output.textContent = "";
    if (resetBtn) resetBtn.style.display = "none";
  }

  function answer(q, btn) {
    var opts = Array.prototype.slice.call(q.querySelectorAll(".quiz-opt"));
    opts.forEach(function (b) { b.disabled = true; });
    btn.classList.add("chosen");

    var correct = btn.getAttribute("data-correct") === "true";
    if (correct) {
      btn.classList.add("is-correct");
      score++;
    } else {
      btn.classList.add("is-wrong");
      var right = q.querySelector('[data-correct="true"]');
      if (right) right.classList.add("is-correct");
    }
    window.setTimeout(function () { advance(q); }, 700);
  }

  function advance(q) {
    var i = qs.indexOf(q);
    q.style.display = "none";
    if (i + 1 < qs.length) {
      qs[i + 1].style.display = "block";
    } else {
      finish();
    }
  }

  function finish() {
    var msg = "Tú: " + score + " de 3 aciertos. ";
    if (score === 3) {
      msg += "Como solo el 19% de los españoles: acertar las tres a la vez.";
    } else {
      msg += "Solo el 19% de los españoles acierta las tres preguntas a la vez.";
    }
    if (output) output.textContent = msg;
    if (resetBtn) resetBtn.style.display = "";
  }

  qs.forEach(function (q) {
    var opts = q.querySelectorAll(".quiz-opt");
    opts.forEach(function (b) {
      b.addEventListener("click", function () { answer(q, b); });
    });
  });

  if (resetBtn) resetBtn.addEventListener("click", init);

  init();
})();
