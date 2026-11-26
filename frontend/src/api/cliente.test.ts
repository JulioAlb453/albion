import { crearCliente, ErrorApi } from "./cliente";

type Respuesta = { status?: number; json?: unknown; cabeceras?: Record<string, string>; cuerpo?: BodyInit | null };

function respuesta({ status = 200, json, cabeceras = {}, cuerpo }: Respuesta = {}): Response {
  const cabecerasFinales = new Headers(cabeceras);
  if (json !== undefined) {
    cabecerasFinales.set("content-type", "application/json");
    return new Response(JSON.stringify(json), { status, headers: cabecerasFinales });
  }
  return new Response(cuerpo ?? null, { status, headers: cabecerasFinales });
}

function armar(...respuestas: (Response | Error)[]) {
  const pila = [...respuestas];
  const fetchFalso = vi.fn(async (_url: string, _opciones?: RequestInit) => {
    const siguiente = pila.shift() ?? respuesta({ status: 204 });
    if (siguiente instanceof Error) throw siguiente;
    return siguiente;
  });
  const alSesionVencida = vi.fn();
  const cliente = crearCliente({
    baseUrl: "http://api.test",
    obtenerToken: () => "token-123",
    alSesionVencida,
    fetchFn: fetchFalso as unknown as typeof fetch,
  });
  return { cliente, fetchFalso, alSesionVencida };
}

const ultimaLlamada = (f: ReturnType<typeof armar>["fetchFalso"]) => {
  const [url, opciones] = f.mock.calls.at(-1)!;
  return { url: new URL(url), opciones: opciones ?? {}, cabeceras: new Headers(opciones?.headers) };
};

/** Espera una promesa que debe fallar y devuelve el ErrorApi, ya con su tipo. */
async function falla(promesa: Promise<unknown>): Promise<ErrorApi> {
  try {
    await promesa;
  } catch (error) {
    return error as ErrorApi;
  }
  throw new Error("Se esperaba que la petición fallara");
}

describe("peticiones", () => {
  it("manda el token y arma la dirección con los parámetros que tienen valor", async () => {
    const { cliente, fetchFalso } = armar(respuesta({ json: [] }));
    await cliente.get("/api/ventas", { ciudad: "Caerleon", tipo: undefined, base_id: "", cantidad: 2, activo: false });
    const { url, cabeceras } = ultimaLlamada(fetchFalso);
    expect(url.origin + url.pathname).toBe("http://api.test/api/ventas");
    expect(Object.fromEntries(url.searchParams)).toEqual({ ciudad: "Caerleon", cantidad: "2", activo: "false" });
    expect(cabeceras.get("authorization")).toBe("Bearer token-123");
  });

  it("lleva la cabecera que evita la página de aviso del dominio gratuito de ngrok", async () => {
    const { cliente, fetchFalso } = armar(respuesta({ json: [] }), respuesta({ json: {} }));
    await cliente.get("/api/ventas");
    expect(ultimaLlamada(fetchFalso).cabeceras.get("ngrok-skip-browser-warning")).toBe("true");
    await cliente.post("/api/ventas", {});
    expect(ultimaLlamada(fetchFalso).cabeceras.get("ngrok-skip-browser-warning")).toBe("true");
  });

  it("envía JSON en POST y PUT", async () => {
    const { cliente, fetchFalso } = armar(respuesta({ json: { id: 1 } }), respuesta({ json: {} }));
    await cliente.post("/api/ventas", { cantidad: 2 });
    let { opciones, cabeceras } = ultimaLlamada(fetchFalso);
    expect(opciones.method).toBe("POST");
    expect(opciones.body).toBe('{"cantidad":2}');
    expect(cabeceras.get("content-type")).toBe("application/json");
    await cliente.put("/api/balance/saldo-inicial", { monto: 1 });
    ({ opciones } = ultimaLlamada(fetchFalso));
    expect(opciones.method).toBe("PUT");
  });

  it("devuelve el JSON de la respuesta y undefined si no hay cuerpo (204)", async () => {
    const { cliente } = armar(respuesta({ json: { id: 7 } }), respuesta({ status: 204 }));
    expect(await cliente.get<{ id: number }>("/x")).toEqual({ id: 7 });
    expect(await cliente.delete("/api/ventas/7")).toBeUndefined();
  });

  it("sube un archivo como formulario sin fijar el tipo de contenido", async () => {
    const { cliente, fetchFalso } = armar(respuesta({ json: { importadas: 2, errores: [] } }));
    const archivo = new File(["a,b"], "ventas.csv", { type: "text/csv" });
    const resultado = await cliente.subir<{ importadas: number }>("/api/ventas/importar", archivo);
    const { opciones, cabeceras } = ultimaLlamada(fetchFalso);
    expect(resultado.importadas).toBe(2);
    expect(opciones.body).toBeInstanceOf(FormData);
    expect((opciones.body as FormData).get("archivo")).toBeInstanceOf(File);
    expect(cabeceras.get("content-type")).toBeNull();  // el navegador agrega el límite del formulario
  });
});

describe("errores", () => {
  it("usa el detalle del servidor como mensaje", async () => {
    const { cliente } = armar(respuesta({ status: 422, json: { detail: "Black Market no admite órdenes de venta" } }));
    await expect(cliente.post("/api/ventas", {})).rejects.toMatchObject({
      name: "ErrorApi", status: 422, message: "Black Market no admite órdenes de venta",
    });
  });

  it("junta los errores de validación de campos en una frase", async () => {
    const detail = [
      { loc: ["body", "cantidad"], msg: "Input should be greater than 0" },
      { loc: ["body", "ciudad"], msg: "Input should be a valid string" },
    ];
    const { cliente } = armar(respuesta({ status: 422, json: { detail } }));
    const error = await falla(cliente.post("/x", {}));
    expect(error.message).toBe("cantidad: Input should be greater than 0; ciudad: Input should be a valid string");
  });

  it("conserva la lista de filas malas de una importación rechazada", async () => {
    const errores = [{ fila: 3, mensaje: "ciudad: 'Narnia' no es válido" }];
    const { cliente } = armar(respuesta({ status: 422, json: { importadas: 0, errores } }));
    const error = await falla(cliente.subir("/api/ventas/importar", new File(["x"], "v.csv")));
    expect(error.errores).toEqual(errores);
    expect(error.message).toMatch(/1 fila/);
  });

  it("un 401 avisa que la sesión venció", async () => {
    const { cliente, alSesionVencida } = armar(respuesta({ status: 401, json: { detail: "La sesión expiró" } }));
    await expect(cliente.get("/api/ventas")).rejects.toMatchObject({ status: 401 });
    expect(alSesionVencida).toHaveBeenCalledOnce();
  });

  it("los demás errores no cierran la sesión", async () => {
    const { cliente, alSesionVencida } = armar(respuesta({ status: 403, json: { detail: "Solo un administrador" } }));
    await expect(cliente.get("/x")).rejects.toMatchObject({ status: 403 });
    expect(alSesionVencida).not.toHaveBeenCalled();
  });

  it("si el servidor no responde, el mensaje dice qué probar", async () => {
    const { cliente } = armar(new TypeError("Failed to fetch"));
    const error = await falla(cliente.get("/x"));
    expect(error).toMatchObject({ status: 0 });
    expect(error.message).toMatch(/No se pudo conectar/);
  });

  it("una respuesta de error sin JSON usa un mensaje genérico con el código", async () => {
    const { cliente } = armar(respuesta({ status: 502, cuerpo: "<html>Bad gateway</html>" }));
    await expect(cliente.get("/x")).rejects.toMatchObject({ status: 502, message: expect.stringContaining("502") });
  });
});

describe("descargas", () => {
  it("devuelve el archivo y el nombre que manda el servidor", async () => {
    const cabeceras = { "content-disposition": 'attachment; filename="ventas-2026-11-25.csv"' };
    const { cliente, fetchFalso } = armar(respuesta({ cuerpo: "a,b\n1,2", cabeceras }));
    const descarga = await cliente.descargar("/api/ventas/exportar", { formato: "csv" });
    expect(descarga.nombre).toBe("ventas-2026-11-25.csv");
    expect(await descarga.archivo.text()).toBe("a,b\n1,2");
    expect(ultimaLlamada(fetchFalso).url.searchParams.get("formato")).toBe("csv");
  });

  it("sin nombre del servidor usa uno por defecto", async () => {
    const { cliente } = armar(respuesta({ cuerpo: "x" }));
    expect((await cliente.descargar("/x")).nombre).toBe("descarga");
  });
});
