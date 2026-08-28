// Cloudflare Pages Function — POST /api/subscribe
// Guarda el email en D1 (binding env.DB). No envía correo, no llama a
// ningún servicio externo. onRequestPost = solo acepta POST; cualquier
// otro método recibe el 405 por defecto de Pages Functions.

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function onRequestPost({ request, env }) {
  const redirect = (path) => Response.redirect(new URL(path, request.url), 302);

  let form;
  try {
    form = await request.formData();
  } catch (err) {
    return redirect('/?e=1');
  }

  // Honeypot: los bots suelen rellenar todos los campos, humanos nunca ven este.
  const honeypot = (form.get('website') || '').toString().trim();
  if (honeypot) {
    return redirect('/gracias/');
  }

  const email = (form.get('email') || '').toString().trim().toLowerCase();
  if (!EMAIL_RE.test(email)) {
    return redirect('/?e=1');
  }

  try {
    await env.DB.prepare(
      `INSERT INTO subscribers (email, created_at, source) VALUES (?1, datetime('now'), 'home') ON CONFLICT(email) DO NOTHING;`
    ).bind(email).run();
  } catch (err) {
    console.error('subscribe: fallo al guardar en D1', err);
  }

  return redirect('/gracias/');
}
