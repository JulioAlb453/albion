/** Todo se muestra con el formato de México: coma para los miles y punto para los decimales. */
const LOCAL = "es-MX";

const ESCALAS: [minimo: number, sufijo: string][] = [
  [1e9, "B"],
  [1e6, "M"],
  [1e3, "k"],
];

const CALIDADES: Record<number, string> = {
  1: "Normal",
  2: "Buena",
  3: "Notable",
  4: "Sobresaliente",
  5: "Obra maestra",
};

/** 120553500 -> "120.6 M". Para los bloques grandes; el valor exacto va aparte (`plataCompleta`). */
export function plataCorta(valor: number): string {
  const escala = ESCALAS.find(([minimo]) => Math.abs(valor) >= minimo);
  if (!escala) return String(Math.round(valor));
  const [minimo, sufijo] = escala;
  return `${Math.round((valor / minimo) * 10) / 10} ${sufijo}`;
}

/** 120553500 -> "120,553,500" */
export function plataCompleta(valor: number): string {
  return new Intl.NumberFormat(LOCAL).format(valor);
}

/** Como `plataCorta`, pero con "+" en los positivos: para variaciones. */
export function signo(valor: number): string {
  return valor > 0 ? `+${plataCorta(valor)}` : plataCorta(valor);
}

export function antiguedad(segundos: number): string {
  if (segundos < 60) return "hace un momento";
  if (segundos < 3_600) return `hace ${Math.floor(segundos / 60)} min`;
  if (segundos < 86_400) return `hace ${Math.floor(segundos / 3_600)} h`;
  return `hace ${Math.floor(segundos / 86_400)} d`;
}

export function etiquetaCalidad(calidad: number): string {
  return CALIDADES[calidad] ?? String(calidad);
}

function partes(dia: string): [number, number, number] {
  const [anio = 0, mes = 1, numero = 1] = dia.split("-").map(Number);
  return [anio, mes - 1, numero];
}

/** El día local de hace `dias` días, como "2026-11-25". */
export function diaLocalHaceDias(dias: number): string {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() - dias);
  const dos = (n: number) => String(n).padStart(2, "0");
  return `${fecha.getFullYear()}-${dos(fecha.getMonth() + 1)}-${dos(fecha.getDate())}`;
}

/** "2026-11-25" (día local) -> el instante en que empieza ese día aquí, en ISO UTC para la API. */
export function inicioDelDia(dia: string): string {
  return new Date(...partes(dia), 0, 0, 0, 0).toISOString();
}

/** "2026-11-25" (día local) -> el último instante de ese día aquí, en ISO UTC para la API. */
export function finDelDia(dia: string): string {
  return new Date(...partes(dia), 23, 59, 59, 999).toISOString();
}

/** "2026-11-25T18:30:00Z" -> "25/11/2026 12:30" en la hora de quien mira. */
export function fechaHora(iso: string): string {
  return new Date(iso)
    .toLocaleString(LOCAL, {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: false,
    })
    .replace(", ", " ");
}

/** "2026-11-25" (día del balance, hora del juego) -> "25 nov". */
export function diaCorto(dia: string): string {
  const [anio, mes, numero] = partes(dia);
  return new Date(anio, mes, numero).toLocaleDateString(LOCAL, { day: "numeric", month: "short" }).replace(".", "");
}
