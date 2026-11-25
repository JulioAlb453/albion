import type { Ciudad, Comparacion, Opcion } from "../api/tipos";

/** La opción (directa u orden) que más rinde en esa ciudad, según la API. */
export function opcionGanadora(comparacion: Comparacion): Opcion | null {
  if (comparacion.mejor === "directa") return comparacion.directa;
  if (comparacion.mejor === "orden") return comparacion.orden;
  return null;
}

/**
 * La primera ciudad con dato reciente (la API ya las manda de mayor a menor neto, con las de dato
 * viejo al final). Si todas son viejas, la primera de la lista: el que llama decide si la corona.
 */
export function mejorCiudad(ciudades: Comparacion[]): Comparacion | null {
  return ciudades.find((c) => c.confiable && opcionGanadora(c)) ?? ciudades[0] ?? null;
}

/** Cuánto más neto paga la mejor ciudad que la de referencia, en %; null si no hay nada que comparar. */
export function ventajaSobre(ciudades: Comparacion[], referencia: Ciudad): number | null {
  const mejor = mejorCiudad(ciudades);
  if (!mejor || mejor.ciudad === referencia) return null;
  const ref = ciudades.find((c) => c.ciudad === referencia);
  const base = ref ? opcionGanadora(ref)?.neto_unitario : undefined;
  const cima = opcionGanadora(mejor)?.neto_unitario;
  if (!base || !cima) return null;
  return ((cima - base) / base) * 100;
}
