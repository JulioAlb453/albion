import { COMANDOS } from "./comandos/indice.js";
import { registrarComandos } from "./registrar.js";

const CONFIG = { token: "tok", clienteId: "111", servidorId: "222", clave: "k".repeat(32), apiUrl: "http://api:8000" };

describe("registrarComandos", () => {
  it("publica los comandos solo en el servidor del gremio, con el token del bot", async () => {
    const fetchFalso = vi.fn(async (_u: string, _o?: RequestInit) => new Response("[]", { status: 200 }));
    await registrarComandos(CONFIG, fetchFalso as unknown as typeof fetch);
    const [url, opciones] = fetchFalso.mock.calls[0]!;
    expect(url).toBe("https://discord.com/api/v10/applications/111/guilds/222/commands");
    expect(opciones?.method).toBe("PUT");
    expect(new Headers(opciones?.headers).get("authorization")).toBe("Bot tok");
    expect(JSON.parse(opciones?.body as string)).toEqual(COMANDOS.map((c) => c.definicion));
  });

  it("si Discord rechaza los comandos, el error dice por qué", async () => {
    const fetchFalso = vi.fn(async () => new Response(JSON.stringify({ message: "Invalid Form Body" }), { status: 400 }));
    await expect(registrarComandos(CONFIG, fetchFalso as unknown as typeof fetch)).rejects.toThrow(/400.*Invalid Form Body/);
  });

  it("el token no aparece en el mensaje de error", async () => {
    const fetchFalso = vi.fn(async () => new Response("tok", { status: 401 }));
    await expect(registrarComandos(CONFIG, fetchFalso as unknown as typeof fetch)).rejects.not.toThrow(/Bot tok/);
  });
});
