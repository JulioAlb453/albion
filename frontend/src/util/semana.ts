import { diaCorto } from "./formato";

// Los pagos semanales van de lunes a domingo en la hora del servidor del juego (UTC).
// Los días se manejan como texto "AAAA-MM-DD" y se calculan en UTC para no depender de la zona de quien mira.

const aFecha = (dia: string) => new Date(`${dia}T00:00:00Z`);
const aTexto = (fecha: Date) => fecha.toISOString().slice(0, 10);

/** El día de hoy según el servidor del juego. */
export const hoyServidor = (ahora: Date = new Date()): string => aTexto(ahora);

export function lunesDe(dia: string): string {
  const fecha = aFecha(dia);
  fecha.setUTCDate(fecha.getUTCDate() - ((fecha.getUTCDay() + 6) % 7));
  return aTexto(fecha);
}

export function moverSemanas(lunes: string, semanas: number): string {
  const fecha = aFecha(lunes);
  fecha.setUTCDate(fecha.getUTCDate() + 7 * semanas);
  return aTexto(fecha);
}

export const domingoDe = (lunes: string): string => {
  const fecha = aFecha(lunes);
  fecha.setUTCDate(fecha.getUTCDate() + 6);
  return aTexto(fecha);
};

/** "2026-11-23" -> "23 nov – 29 nov". */
export const etiquetaSemana = (lunes: string): string => `${diaCorto(lunes)} – ${diaCorto(domingoDe(lunes))}`;
