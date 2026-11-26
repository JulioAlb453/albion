import { Client, Events, GatewayIntentBits } from "discord.js";
import { crearApi } from "./api.js";
import { ErrorConfig, leerConfig } from "./config.js";
import { autocompletarObjeto, despachar } from "./despachador.js";
import type { InteraccionAutocompletar, InteraccionComando } from "./interacciones.js";
import { registrarComandos } from "./registrar.js";

async function main(): Promise<void> {
  const config = leerConfig();
  const fabrica = crearApi({ baseUrl: config.apiUrl, clave: config.clave });

  await registrarComandos(config);
  console.log("Comandos publicados en el servidor del gremio.");

  const cliente = new Client({ intents: [GatewayIntentBits.Guilds] });

  cliente.on(Events.InteractionCreate, (interaccion) => {
    // discord.js cumple estas formas; los tipos propios solo piden lo que los comandos usan
    if (interaccion.isChatInputCommand()) {
      void despachar(interaccion as unknown as InteraccionComando, fabrica);
    } else if (interaccion.isAutocomplete()) {
      void autocompletarObjeto(interaccion as unknown as InteraccionAutocompletar, fabrica);
    }
  });

  cliente.once(Events.ClientReady, (listo) => console.log(`Bot conectado como ${listo.user.tag}`));

  const apagar = () => {
    void cliente.destroy().finally(() => process.exit(0));
  };
  process.on("SIGTERM", apagar);
  process.on("SIGINT", apagar);

  await cliente.login(config.token);
}

main().catch((error: unknown) => {
  // nunca se imprime la configuración completa: lleva el token
  console.error(error instanceof ErrorConfig ? `Configuración incompleta: ${error.message}` : error);
  process.exit(1);
});
