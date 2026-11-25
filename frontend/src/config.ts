/** Dirección de la API. En producción es el dominio fijo de ngrok (con https). */
export const URL_API: string = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
