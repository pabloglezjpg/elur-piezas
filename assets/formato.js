/* ============================================================
   piezas.elur.es — formato de número en español. Fuente única.

   Existe porque el sitio ya se ha tropezado dos veces con lo mismo:

   1. toLocaleString("es-ES") NO agrupa los millares de cuatro
      cifras: 6600 sale «6600», no «6.600». En una pieza hubo que
      dejar la cifra estática para que el gráfico no contradijera
      al cuerpo.
   2. El ICU de algunos navegadores no aplica separador de millares
      en es-ES aunque declare soportar el locale, así que otra pieza
      acabó escribiendo su propio formateador a mano.

   Norma de la casa: millares con punto SIEMPRE (también con cuatro
   cifras), decimales con coma, y el signo de porcentaje pegado al
   número. Sin dependencias y sin ICU: el resultado no cambia entre
   navegadores.
   ============================================================ */
(function (global) {
  "use strict";

  function numero(n, decimales) {
    var v = Number(n);
    if (!isFinite(v)) return String(n);
    var dec = decimales == null ? (Number.isInteger(v) ? 0 : 2) : decimales;
    var negativo = v < 0 || Object.is(v, -0);
    var fijo = Math.abs(v).toFixed(dec);
    var partes = fijo.split(".");
    var entera = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    var salida = dec > 0 ? entera + "," + partes[1] : entera;
    return (negativo && Number(fijo) !== 0 ? "−" : "") + salida;
  }

  function moneda(n, decimales, simbolo) {
    return numero(n, decimales) + " " + (simbolo || "€");
  }

  function porcentaje(n, decimales) {
    return numero(n, decimales) + "%";
  }

  global.Formato = { numero: numero, moneda: moneda, porcentaje: porcentaje };
})(typeof window !== "undefined" ? window : this);
