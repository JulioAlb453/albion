/** `URL_API` se calcula al cargar el módulo, así que cada caso lo vuelve a importar. */
async function cargar(valor: string | undefined) {
  vi.resetModules();
  if (valor === undefined) vi.stubEnv("VITE_API_URL", undefined as unknown as string);
  else vi.stubEnv("VITE_API_URL", valor);
  return (await import("./config")).URL_API;
}

afterEach(() => vi.unstubAllEnvs());

describe("URL_API", () => {
  it("usa la dirección configurada", async () => {
    expect(await cargar("https://gremio.ngrok.app")).toBe("https://gremio.ngrok.app");
  });

  it("le quita la barra final, para no armar direcciones con //", async () => {
    expect(await cargar("https://gremio.ngrok.app/")).toBe("https://gremio.ngrok.app");
  });

  it("sin configurar usa la API local", async () => {
    expect(await cargar(undefined)).toBe("http://localhost:8000");
  });

  it("una variable vacía también usa la API local (así llega desde GitHub si no se definió)", async () => {
    expect(await cargar("")).toBe("http://localhost:8000");
  });

  it("espacios en blanco tampoco cuentan como una dirección", async () => {
    expect(await cargar("   ")).toBe("http://localhost:8000");
  });
});
