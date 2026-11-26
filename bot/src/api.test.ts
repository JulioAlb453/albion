import { crearApi, ErrorApi } from "./api.js";
import { VENTA } from "./pruebas/datos.js";

const CLAVE = "k".repeat(32);
const USUARIO = { id: "123", username: "julio", globalName: "Julio Ávila", avatar: "abc" };

function armar(...respuestas: (Response | Error)[]) {
  const pila = [...respuestas];
  const fetchFalso = vi.fn(async (_url: string, _o?: RequestInit) => {
    const siguiente = pila.shift() ?? new Response("[]", { headers: { "content-type": "application/json" } });
    if (siguiente instanceof Error) throw siguiente;
    return siguiente;
  });
  const api = crearApi({ baseUrl: "http://api:8000", clave: CLAVE, fetchFn: fetchFalso as unknown as typeof fetch }).como(USUARIO);
  const ultima = () => {
    const [url, opciones] = fetchFalso.mock.calls.at(-1)!;
    return { url: new URL(url), metodo: opciones?.method ?? "GET", cabeceras: new Headers(opciones?.headers), cuerpo: opciones?.body };
  };
  return { api, ultima };
}
const json = (cuerpo: unknown, status = 200) => new Response(JSON.stringify(cuerpo), { status, headers: { "content-type": "application/json" } });

describe("cabeceras", () => {
  it("se identifica con la clave y con quien usó el comando (nombre con tildes codificado)", async () => {
    const { api, ultima } = armar();
    await api.buscarObjetos("espada");
    const { cabeceras } = ultima();
    expect(cabeceras.get("x-bot-clave")).toBe(CLAVE);
    expect(cabeceras.get("x-discord-id")).toBe("123");
    expect(decodeURIComponent(cabeceras.get("x-discord-nombre")!)).toBe("Julio Ávila");
    expect(cabeceras.get("x-discord-avatar")).toBe("abc");
  });

  it("sin nombre global usa el de usuario, y no manda avatar si no tiene", async () => {
    const api = crearApi({ baseUrl: "http://api:8000", clave: CLAVE, fetchFn: vi.fn(async () => json([])) as unknown as typeof fetch });
    const fetchFalso = vi.fn(async () => json([]));
    await crearApi({ baseUrl: "http://api:8000", clave: CLAVE, fetchFn: fetchFalso as unknown as typeof fetch })
      .como({ id: "9", username: "ana", globalName: null, avatar: null }).buscarObjetos("x");
    const cabeceras = new Headers((fetchFalso.mock.calls[0] as unknown as [string, RequestInit])[1].headers);
    expect(decodeURIComponent(cabeceras.get("x-discord-nombre")!)).toBe("ana");
    expect(cabeceras.has("x-discord-avatar")).toBe(false);
    expect(api).toBeDefined();
  });
});

describe("llamadas", () => {
  it("busca objetos en el catálogo", async () => {
    const { api, ultima } = armar(json([{ base_id: "T6_MAIN_SWORD" }]));
    expect(await api.buscarObjetos("espada ancha")).toEqual([{ base_id: "T6_MAIN_SWORD" }]);
    expect(ultima().url.pathname).toBe("/api/catalogo");
    expect(Object.fromEntries(ultima().url.searchParams)).toEqual({ q: "espada ancha", limite: "25" });
  });

  it("pide un objeto por su identificador", async () => {
    const { api, ultima } = armar(json({ base_id: "T6_MAIN_SWORD" }));
    await api.obtenerObjeto("T6_MAIN_SWORD");
    expect(ultima().url.pathname).toBe("/api/catalogo/T6_MAIN_SWORD");
  });

  it("compara con los cuatro parámetros", async () => {
    const { api, ultima } = armar();
    await api.comparar({ base_id: "T6_MAIN_SWORD", encantamiento: 2, calidad: 4, cantidad: 3 });
    expect(ultima().url.pathname).toBe("/api/mercado/comparar");
    expect(Object.fromEntries(ultima().url.searchParams)).toEqual({ base_id: "T6_MAIN_SWORD", encantamiento: "2", calidad: "4", cantidad: "3" });
  });

  it("registra una venta con un cuerpo JSON", async () => {
    const { api, ultima } = armar(json(VENTA, 201));
    const nueva = { base_id: "T6_MAIN_SWORD", encantamiento: 2, calidad: 4, ciudad: "Fort Sterling" as const, tipo: "orden" as const, cantidad: 1, precio_unitario: 100_000 };
    expect((await api.registrarVenta(nueva)).neto).toBe(93_500);
    expect(ultima().metodo).toBe("POST");
    expect(ultima().cabeceras.get("content-type")).toBe("application/json");
    expect(JSON.parse(ultima().cuerpo as string)).toEqual(nueva);
  });

  it("pide los reportes de un periodo", async () => {
    const { api, ultima } = armar(json({}));
    await api.reportes("2026-11-01T00:00:00Z");
    expect(ultima().url.searchParams.get("desde")).toBe("2026-11-01T00:00:00Z");
  });

  it("sin saldo inicial (404) devuelve null, y sin evolución, una lista vacía", async () => {
    const { api } = armar(json({ detail: "x" }, 404), json({ detail: "x" }, 404));
    expect(await api.saldoInicial()).toBeNull();
    expect(await api.evolucion()).toEqual([]);
  });
});

describe("errores", () => {
  it("usa el detalle que manda la API y conserva el código", async () => {
    const { api } = armar(json({ detail: "Solo un administrador puede hacer esta operación" }, 403));
    await expect(api.registrarGasto({ categoria: "reparaciones", descripcion: "", monto: 1 })).rejects.toMatchObject({
      name: "ErrorApi", status: 403, message: "Solo un administrador puede hacer esta operación",
    });
  });

  it("junta los errores de validación de campos", async () => {
    const detail = [{ loc: ["body", "cantidad"], msg: "Input should be greater than 0" }];
    const { api } = armar(json({ detail }, 422));
    await expect(api.registrarVenta({} as never)).rejects.toThrow("cantidad: Input should be greater than 0");
  });

  it("si la API no responde, lo dice con un mensaje entendible", async () => {
    const { api } = armar(new TypeError("fetch failed"));
    const error = await api.buscarObjetos("x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ErrorApi);
    expect(error).toMatchObject({ status: 0, message: expect.stringContaining("No pude conectar") });
  });

  it("una respuesta de error sin JSON usa un mensaje con el código", async () => {
    const { api } = armar(new Response("<html>", { status: 502 }));
    await expect(api.buscarObjetos("x")).rejects.toThrow("502");
  });
});
