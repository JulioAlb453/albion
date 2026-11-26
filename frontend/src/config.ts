/**
 * Dirección de la API. En producción es el dominio fijo de ngrok (con https).
 *
 * Una variable vacía cuenta como "no configurada": en GitHub Actions una variable que no se
 * definió llega como texto vacío (no como undefined), y con `??` se habría quedado el vacío.
 */
export const URL_API: string = (import.meta.env.VITE_API_URL?.trim() || "http://localhost:8000").replace(/\/$/, "");
