import { ErrorConfig, leerConfig } from "./config.js";

const BASE = { DISCORD_TOKEN: "token", DISCORD_CLIENT_ID: "111", DISCORD_GUILD_ID: "222", BOT_CLAVE: "k".repeat(32) };

describe("leerConfig", () => {
  it("lee las variables y usa la API local si no se indica otra", () => {
    expect(leerConfig(BASE)).toEqual({
      token: "token", clienteId: "111", servidorId: "222", clave: "k".repeat(32), apiUrl: "http://localhost:8000",
    });
  });

  it("quita la barra final de la dirección de la API", () => {
    expect(leerConfig({ ...BASE, API_URL: "http://api:8000/" }).apiUrl).toBe("http://api:8000");
  });

  it("si faltan variables dice cuáles, todas juntas", () => {
    expect(() => leerConfig({ DISCORD_CLIENT_ID: "1" })).toThrow(ErrorConfig);
    expect(() => leerConfig({ DISCORD_CLIENT_ID: "1" })).toThrow(/DISCORD_TOKEN.*DISCORD_GUILD_ID.*BOT_CLAVE/);
  });

  it("un valor en blanco cuenta como que falta", () => {
    expect(() => leerConfig({ ...BASE, DISCORD_TOKEN: "   " })).toThrow(/DISCORD_TOKEN/);
  });

  it("la clave del bot debe ser larga, porque protege la API", () => {
    expect(() => leerConfig({ ...BASE, BOT_CLAVE: "corta" })).toThrow(/BOT_CLAVE.*32/);
  });
});
