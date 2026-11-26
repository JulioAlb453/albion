/** 120 553 500 -> "120.6 M". Es lo que cabe en una línea de Discord. */
export function plataCorta(valor: number): string {
  const abs = Math.abs(valor);
  const escala = abs >= 1e9 ? [1e9, " B"] : abs >= 1e6 ? [1e6, " M"] : abs >= 1e3 ? [1e3, " k"] : [1, ""];
  const numero = Math.round((valor / (escala[0] as number)) * 10) / 10;
  return `${numero}${escala[1]}`;
}

export const plataCompleta = (valor: number): string => valor.toLocaleString("en-US");

export const signo = (valor: number): string => (valor > 0 ? `+${plataCorta(valor)}` : plataCorta(valor));

export function antiguedad(segundos: number): string {
  if (segundos < 60) return "hace un momento";
  if (segundos < 3_600) return `hace ${Math.floor(segundos / 60)} min`;
  if (segundos < 86_400) return `hace ${Math.floor(segundos / 3_600)} h`;
  return `hace ${Math.floor(segundos / 86_400)} d`;
}

const CALIDADES = ["Normal", "Buena", "Notable", "Sobresaliente", "Obra maestra"];
export const etiquetaCalidad = (calidad: number): string => CALIDADES[calidad - 1] ?? `Calidad ${calidad}`;
