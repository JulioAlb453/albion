import { ErrorApi } from "./api.js";
import { EFIMERO } from "./comandos/comando.js";
import { COMANDOS } from "./comandos/indice.js";
import type { InteraccionAutocompletar, InteraccionComando } from "./interacciones.js";
import { CATEGORIAS_OBJETO, type ClienteApi, type UsuarioDiscord } from "./tipos.js";

/** Da una API ya identificada con quien usó el comando. */
export interface FabricaApi {
  como(usuario: UsuarioDiscord): ClienteApi;
}

export async function despachar(i: InteraccionComando, fabrica: FabricaApi, ahora: () => Date = () => new Date()): Promise<void> {
  const comando = COMANDOS.find((c) => c.definicion.name === i.commandName);
  try {
    if (!comando) {
      await i.deferReply({ flags: EFIMERO });
      await i.editReply("Ese comando no lo conozco. Puede que el bot esté desactualizado.");
      return;
    }
    await comando.ejecutar(i, { api: fabrica.como(i.user), ahora });
  } catch (error) {
    const mensaje = error instanceof ErrorApi ? error.message : "Ups, algo salió mal. Inténtalo de nuevo en un momento.";
    if (!(error instanceof ErrorApi)) console.error(`Falló /${i.commandName}:`, error);
    try {
      await i.editReply(mensaje);
    } catch {
      /* la interacción ya expiró; no hay a quién avisar */
    }
  }
}

export async function autocompletarObjeto(i: InteraccionAutocompletar, fabrica: FabricaApi): Promise<void> {
  const texto = i.options.getFocused().trim();
  if (!texto) return void (await i.respond([]));
  try {
    const objetos = await fabrica.como(i.user).buscarObjetos(texto);
    await i.respond(
      objetos.slice(0, 25).map((o) => ({
        name: `${o.nombre} · ${CATEGORIAS_OBJETO[o.categoria]} · ${o.base_id}`.slice(0, 100),
        value: o.base_id,
      })),
    );
  } catch {
    await i.respond([]);
  }
}
