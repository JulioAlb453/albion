/** La sesión es el token que devuelve la API tras iniciar sesión con Discord. */

const CLAVE = "gremio.token";

/** El regreso de Discord llega en el fragmento: `#token=...` o `#error=...`. */
export function leerFragmento(hash: string): { token?: string; error?: string } {
  const texto = hash.replace(/^#/, "");
  if (texto.startsWith("token=")) return { token: texto.slice("token=".length) };
  if (texto.startsWith("error=")) return { error: texto.slice("error=".length) };
  return {};
}

/** Cuándo vence el token, en milisegundos; solo para avisar a tiempo, la API es quien manda. */
export function expiracionDe(token: string): number | null {
  const partes = token.split(".");
  if (partes.length !== 3) return null;
  try {
    const base64 = (partes[1] ?? "").replace(/-/g, "+").replace(/_/g, "/");
    const carga = JSON.parse(atob(base64 + "=".repeat((4 - (base64.length % 4)) % 4)));
    return typeof carga.exp === "number" ? carga.exp * 1000 : null;
  } catch {
    return null;
  }
}

export function guardarToken(token: string): void {
  try {
    localStorage.setItem(CLAVE, token);
  } catch {
    // Sin almacenamiento (modo privado estricto): la sesión dura hasta recargar la página.
  }
}

export function leerToken(): string | null {
  try {
    const token = localStorage.getItem(CLAVE);
    if (!token) return null;
    const vence = expiracionDe(token);
    if (vence === null || vence <= Date.now()) {
      localStorage.removeItem(CLAVE);
      return null;
    }
    return token;
  } catch {
    return null;
  }
}

export function borrarToken(): void {
  try {
    localStorage.removeItem(CLAVE);
  } catch {
    // nada que borrar
  }
}

/**
 * Recoge el resultado del inicio de sesión que viene en la dirección y la deja limpia,
 * para que el token no se quede en la barra del navegador ni en el historial.
 */
export function iniciarDesdeUrl(): { error?: string } {
  const { token, error } = leerFragmento(window.location.hash);
  if (token === undefined && error === undefined) return { error: undefined };
  if (token !== undefined) guardarToken(token);
  window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}#/`);
  return { error };
}
