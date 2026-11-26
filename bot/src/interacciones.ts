import type { UsuarioDiscord } from "./tipos.js";

/** Lo mínimo de una interacción de discord.js que usan los comandos: así se prueban sin Discord. */
export interface Opciones {
  getString(nombre: string): string | null;
  getInteger(nombre: string): number | null;
}

export interface InteraccionComando {
  commandName: string;
  user: UsuarioDiscord;
  options: Opciones;
  deferReply(opciones: { flags: number }): Promise<unknown>;
  editReply(contenido: Contenido): Promise<unknown>;
  followUp(contenido: Contenido): Promise<unknown>;
}

export interface InteraccionAutocompletar {
  commandName: string;
  user: UsuarioDiscord;
  options: { getFocused(): string };
  respond(opciones: { name: string; value: string }[]): Promise<unknown>;
}

export type Contenido = string | { content?: string; embeds?: Embed[] };

export interface Embed {
  title?: string;
  description?: string;
  color?: number;
  fields?: { name: string; value: string; inline?: boolean }[];
  footer?: { text: string };
}
