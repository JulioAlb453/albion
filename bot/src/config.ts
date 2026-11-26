export class ErrorConfig extends Error {
  override name = "ErrorConfig";
}

export interface Config {
  token: string;
  clienteId: string;
  servidorId: string;
  clave: string;
  apiUrl: string;
}

type Entorno = Record<string, string | undefined>;

export function leerConfig(entorno: Entorno = process.env): Config {
  const valor = (nombre: string) => entorno[nombre]?.trim() ?? "";
  const requeridas = ["DISCORD_TOKEN", "DISCORD_CLIENT_ID", "DISCORD_GUILD_ID", "BOT_CLAVE"];
  const faltan = requeridas.filter((n) => !valor(n));
  if (faltan.length) throw new ErrorConfig(`Faltan variables de entorno: ${faltan.join(", ")}`);
  if (valor("BOT_CLAVE").length < 32) throw new ErrorConfig("BOT_CLAVE debe tener al menos 32 caracteres");
  return {
    token: valor("DISCORD_TOKEN"),
    clienteId: valor("DISCORD_CLIENT_ID"),
    servidorId: valor("DISCORD_GUILD_ID"),
    clave: valor("BOT_CLAVE"),
    apiUrl: (valor("API_URL") || "http://localhost:8000").replace(/\/$/, ""),
  };
}
