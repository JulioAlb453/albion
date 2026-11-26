import { ErrorApi } from "./api.js";
import { COMANDOS } from "./comandos/indice.js";
import { autocompletarObjeto, despachar } from "./despachador.js";
import { ARTEFACTO, ESPADA } from "./pruebas/datos.js";
import { apiFalsa, autocompletado, interaccion } from "./pruebas/falsos.js";

const fabrica = (api: ReturnType<typeof apiFalsa>) => ({ como: () => api });
const ahora = () => new Date("2026-11-25T12:00:00Z");
const SIN_REPORTE = {
  ganancia_por_objeto: [], impuestos: { impuesto_venta: 0, tarifa_publicacion: 0, total: 0 },
  gastos_por_categoria: [], ventas_netas: 0, gastos_totales: 0, resultado: 0,
  ingresos_extra: 0, ingresos_por_categoria: [], pagos_semanales: 0,
};

describe("definiciones (límites de Discord)", () => {
  it("son los cinco comandos esperados", () => {
    expect(COMANDOS.map((c) => c.definicion.name).sort()).toEqual(["balance", "comparar", "gasto", "precio", "venta"]);
  });

  it.each(COMANDOS.map((c) => [c.definicion.name, c] as const))("%s respeta nombres, descripciones y orden de opciones", (_n, c) => {
    const d = c.definicion;
    expect(d.name).toMatch(/^[\p{Ll}\p{N}_-]{1,32}$/u);
    expect(d.description.length).toBeGreaterThan(0);
    expect(d.description.length).toBeLessThanOrEqual(100);
    const opciones = d.options ?? [];
    expect(opciones.length).toBeLessThanOrEqual(25);
    let hayOpcional = false;
    for (const o of opciones) {
      expect(o.name).toMatch(/^[\p{Ll}\p{N}_-]{1,32}$/u);
      expect(o.description.length).toBeLessThanOrEqual(100);
      expect(o.choices?.length ?? 0).toBeLessThanOrEqual(25);
      if (!o.required) hayOpcional = true;
      else expect(hayOpcional, `${o.name}: las requeridas van antes que las opcionales`).toBe(false);
    }
  });

  it("los comandos de escritura se anuncian como solo para administradores", () => {
    for (const nombre of ["venta", "gasto"]) {
      expect(COMANDOS.find((c) => c.definicion.name === nombre)!.definicion.description).toMatch(/admin/i);
    }
  });
});

describe("despachar", () => {
  it("manda el comando a su implementación con la API de quien lo usó", async () => {
    const api = apiFalsa({ saldoInicial: async () => null, evolucion: async () => [], reportes: async () => SIN_REPORTE });
    const { i, llamadas } = interaccion();
    i.commandName = "balance";
    await despachar(i, fabrica(api), ahora);
    expect(llamadas.some((l) => l.tipo === "edit")).toBe(true);
  });

  it("un comando desconocido se responde en privado", async () => {
    const { i, texto, llamadas } = interaccion();
    i.commandName = "nada";
    await despachar(i, fabrica(apiFalsa()), ahora);
    expect(llamadas[0]).toMatchObject({ tipo: "defer", opciones: { flags: 64 } });
    expect(texto()).toContain("no lo conozco");
  });

  it("un error de la API llega al usuario en palabras, no como traza", async () => {
    const api = apiFalsa({ saldoInicial: async () => { throw new ErrorApi(0, "No pude conectar con la API del gremio."); } });
    const { i, texto } = interaccion();
    i.commandName = "balance";
    await despachar(i, fabrica(api), ahora);
    expect(texto()).toContain("No pude conectar");
  });

  it("un fallo inesperado no se filtra: mensaje genérico", async () => {
    const api = apiFalsa({ saldoInicial: async () => { throw new Error("secreto interno ABC"); } });
    const { i, texto } = interaccion();
    i.commandName = "balance";
    await despachar(i, fabrica(api), ahora);
    expect(texto()).not.toContain("secreto interno");
    expect(texto()).toContain("algo salió mal");
  });
});

describe("autocompletar objeto", () => {
  it("ofrece hasta 25 opciones con nombre ≤100 y el base_id como valor", async () => {
    const muchos = Array.from({ length: 40 }, (_, n) => ({ ...ESPADA, base_id: `T6_X${n}`, nombre: "N".repeat(150) }));
    const api = apiFalsa({ buscarObjetos: async () => muchos });
    const { i, respuestas } = autocompletado("esp");
    await autocompletarObjeto(i, fabrica(api));
    expect(api.buscarObjetos).toHaveBeenCalledWith("esp");
    expect(respuestas[0]).toHaveLength(25);
    expect(respuestas[0]![0]!.name.length).toBeLessThanOrEqual(100);
    expect(respuestas[0]![0]!.value).toBe("T6_X0");
  });

  it("muestra la categoría para distinguir objetos parecidos", async () => {
    const api = apiFalsa({ buscarObjetos: async () => [ESPADA, ARTEFACTO] });
    const { i, respuestas } = autocompletado("a");
    await autocompletarObjeto(i, fabrica(api));
    expect(respuestas[0]!.map((o) => o.name).join("|")).toContain("Artefacto");
  });

  it("si la API falla responde una lista vacía en vez de dejar colgado a Discord", async () => {
    const api = apiFalsa({ buscarObjetos: async () => { throw new ErrorApi(0, "x"); } });
    const { i, respuestas } = autocompletado("a");
    await autocompletarObjeto(i, fabrica(api));
    expect(respuestas).toEqual([[]]);
  });

  it("con texto vacío no consulta", async () => {
    const api = apiFalsa();
    const { i, respuestas } = autocompletado("  ");
    await autocompletarObjeto(i, fabrica(api));
    expect(respuestas).toEqual([[]]);
    expect(api.buscarObjetos).not.toHaveBeenCalled();
  });
});
