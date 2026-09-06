// Cloudflare Pages · cierra los ficheros internos que el despliegue sirve en abierto.
//
// POR QUÉ NO BASTA CON _redirects. Medido en producción el 7 de septiembre de 2026, con
// el fichero desplegado y su canario respondiendo 308: las SIETE rutas cuyo fichero
// existe seguían devolviendo 200 —/CLAUDE.md con sus 38.150 bytes— y la única que daba
// 404 era /_BRIEFING_COWORK_piezas.md, que no existe porque está en .gitignore. En Pages,
// un fichero que existe gana a su regla de _redirects. Las Functions corren antes que los
// assets; las reglas de _redirects, no.
//
// LA FRONTERA DE LO INTERNO ES EL DIRECTORIO, NO LA EXTENSIÓN. herramientas/lib/ lleva un
// sonda_overflow.js, y una lista blanca por extensión no lo habría cazado nunca: .js está
// en la lista buena. Por eso lib/ se cierra entero, arbol.py incluido.
//
// LO QUE SE QUEDA PÚBLICO, Y A PROPÓSITO: <slug>/datos.json y herramientas/*.py.
// Publicar cómo se comprueba una pieza es el argumento; el andamio interno del gate, no.
//
// DOS RUTAS SE CIERRAN ANTES DE EXISTIR, a propósito: despliegue.json y
// retiradas_sin_declarar.json las va a crear el gate. Cerrarlas por adelantado no cuesta
// nada y evita la ventana en que existen y están abiertas, que es como se coló todo esto.

const CERRADOS = new Set([
  '/CLAUDE.md',
  '/FLUJO.md',
  '/_BRIEFING_COWORK_piezas.md',
  '/schema.sql',
  '/.gitignore',
  '/herramientas/sin_declarar.json',
  '/herramientas/deriva_tarjeta.json',
  '/herramientas/superficies.json',
  '/herramientas/despliegue.json',
  '/herramientas/retiradas_sin_declarar.json',
]);

const PREFIJOS_CERRADOS = ['/herramientas/lib/'];

export async function onRequest(context) {
  // Salida rápida primero: si algo falla más abajo, que sea en el 1% de las peticiones
  // y no en todas. Este middleware corre en CADA petición del sitio.
  const ruta = new URL(context.request.url).pathname;
  const cerrada =
    CERRADOS.has(ruta) || PREFIJOS_CERRADOS.some((p) => ruta.startsWith(p));
  if (!cerrada) return context.next();

  try {
    const pagina = await context.env.ASSETS.fetch(
      new URL('/404.html', context.request.url)
    );
    return new Response(pagina.body, {
      status: 404,
      headers: { 'content-type': 'text/html; charset=utf-8' },
    });
  } catch {
    return new Response('Not found', { status: 404 });
  }
}
