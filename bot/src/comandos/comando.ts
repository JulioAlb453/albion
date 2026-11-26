import type { InteraccionComando } from "../interacciones.js";
import type { Contexto } from "../tipos.js";

/** Tipos de opción de Discord que usamos (ApplicationCommandOptionType). */
export const TIPO_OPCION = { texto: 3, entero: 4 } as const;

export interface OpcionDefinicion {
  name: string;
  description: string;
  type: number;
  required?: boolean;
  autocomplete?: boolean;
  choices?: { name: string; value: string }[];
  min_value?: number;
  max_value?: number;
}

export interface Definicion {
  name: string;
  description: string;
  options?: OpcionDefinicion[];
}

export interface Comando {
  definicion: Definicion;
  ejecutar(interaccion: InteraccionComando, contexto: Contexto): Promise<void>;
}

/** Bandera de Discord: solo la ve quien usó el comando. */
export const EFIMERO = 64;

export const COLOR = { info: 0x4f8cff, bien: 0x3ecf8e, aviso: 0xf5a524 } as const;

export const OPCION_OBJETO: OpcionDefinicion = {
  name: "objeto", description: "Escribe para buscar en el catálogo", type: TIPO_OPCION.texto, required: true, autocomplete: true,
};
export const OPCION_ENCANTAMIENTO: OpcionDefinicion = {
  name: "encantamiento", description: "Nivel de encantamiento (0 a 4)", type: TIPO_OPCION.entero, min_value: 0, max_value: 4,
};
export const OPCION_CALIDAD: OpcionDefinicion = {
  name: "calidad", description: "1 Normal · 2 Buena · 3 Notable · 4 Sobresaliente · 5 Obra maestra", type: TIPO_OPCION.entero, min_value: 1, max_value: 5,
};
