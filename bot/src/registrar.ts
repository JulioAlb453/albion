import type { Config } from "./config.js";
import { COMANDOS } from "./comandos/indice.js";

/**
 * Publica los comandos en el servidor del gremio (PUT reemplaza la lista entera).
 * Por servidor y no global: aparecen al instante y no existen en ningún otro lado.
 */
export async function registrarComandos(config: Config, fetchFn: typeof fetch = fetch): Promise<void> {
  const url = `https://discord.com/api/v10/applications/${config.clienteId}/guilds/${config.servidorId}/commands`;
  const r = await fetchFn(url, {
    method: "PUT",
    headers: { authorization: `Bot ${config.token}`, "content-type": "application/json" },
    body: JSON.stringify(COMANDOS.map((c) => c.definicion)),
  });
  if (!r.ok) {
    let detalle = "";
    try {
      detalle = ((await r.json()) as { message?: string }).message ?? "";
    } catch {
      /* sin JSON */
    }
    throw new Error(`Discord rechazó los comandos (${r.status}) ${detalle}`.trim());
  }
}
