import type { InteraccionAutocompletar, InteraccionComando } from "../interacciones.js";
import type { ClienteApi, Contexto, UsuarioDiscord } from "../tipos.js";

export type Llamada = { tipo: "defer" | "edit" | "followUp"; contenido?: any; opciones?: any };

/** Una interacción de mentira: guarda lo que el comando responde. Las opciones se dan por nombre. */
export function interaccion(opciones: Record<string, string | number | undefined> = {}, usuario: Partial<UsuarioDiscord> = {}) {
  const llamadas: Llamada[] = [];
  const i: InteraccionComando = {
    commandName: "x",
    user: { id: "1", username: "julio", globalName: "Julio", avatar: null, ...usuario },
    options: {
      getString: (nombre) => (typeof opciones[nombre] === "string" ? (opciones[nombre] as string) : null),
      getInteger: (nombre) => (typeof opciones[nombre] === "number" ? (opciones[nombre] as number) : null),
    },
    deferReply: async (o) => void llamadas.push({ tipo: "defer", opciones: o }),
    editReply: async (c) => void llamadas.push({ tipo: "edit", contenido: c }),
    followUp: async (c) => void llamadas.push({ tipo: "followUp", contenido: c }),
  };
  /** Todo lo que se respondió, como texto, para buscar frases sin importar el formato. */
  const texto = () => JSON.stringify(llamadas.filter((l) => l.contenido).map((l) => l.contenido));
  return { i, llamadas, texto, ediciones: () => llamadas.filter((l) => l.tipo === "edit"), publicas: () => llamadas.filter((l) => l.tipo === "followUp") };
}

export function autocompletado(enfoque: string) {
  const respuestas: { name: string; value: string }[][] = [];
  const i: InteraccionAutocompletar = {
    commandName: "precio",
    user: { id: "1", username: "julio", globalName: "Julio", avatar: null },
    options: { getFocused: () => enfoque },
    respond: async (opciones) => void respuestas.push(opciones),
  };
  return { i, respuestas };
}

const NO_ESPERADA = (nombre: string) => async () => {
  throw new Error(`El comando llamó a ${nombre}, que no se esperaba`);
};

/** Una API de mentira: lo que no se indica falla, para que cada prueba declare lo que usa. */
export function apiFalsa(implementaciones: Partial<ClienteApi> = {}): ClienteApi & { [K in keyof ClienteApi]: ReturnType<typeof vi.fn> } {
  const nombres = ["buscarObjetos", "obtenerObjeto", "comparar", "saldoInicial", "evolucion", "reportes", "registrarVenta", "registrarGasto"] as const;
  const api: Record<string, unknown> = {};
  for (const nombre of nombres) api[nombre] = vi.fn(implementaciones[nombre] ?? NO_ESPERADA(nombre));
  return api as unknown as ReturnType<typeof apiFalsa>;
}

export const AHORA = new Date("2026-11-25T12:00:00Z");
export const contexto = (api: ClienteApi): Contexto => ({ api, ahora: () => AHORA });
