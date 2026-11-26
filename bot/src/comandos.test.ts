import { balance } from "./comandos/balance.js";
import { comparar } from "./comandos/comparar.js";
import { gasto } from "./comandos/gasto.js";
import { precio } from "./comandos/precio.js";
import { venta } from "./comandos/venta.js";
import { ErrorApi } from "./api.js";
import { despachar } from "./despachador.js";
import { ARTEFACTO, COMPARACIONES, ESPADA, VENTA } from "./pruebas/datos.js";
import { apiFalsa, contexto, interaccion } from "./pruebas/falsos.js";

const EFIMERO = 64;
const SIN_REPORTE = {
  ganancia_por_objeto: [], impuestos: { impuesto_venta: 0, tarifa_publicacion: 0, total: 0 },
  gastos_por_categoria: [], ventas_netas: 0, gastos_totales: 0, resultado: 0,
};

describe("/precio", () => {
  it("responde solo a quien preguntó, con la mejor opción por ciudad y el Black Market primero", async () => {
    const api = apiFalsa({ obtenerObjeto: async () => ESPADA, comparar: async () => COMPARACIONES });
    const { i, llamadas, texto } = interaccion({ objeto: "T6_MAIN_SWORD", encantamiento: 2, calidad: 4 });
    await precio.ejecutar(i, contexto(api));
    expect(llamadas[0]).toMatchObject({ tipo: "defer", opciones: { flags: EFIMERO } });
    expect(api.comparar).toHaveBeenCalledWith({ base_id: "T6_MAIN_SWORD", encantamiento: 2, calidad: 4, cantidad: 1 });
    const t = texto();
    expect(t).toContain("Espada ancha del maestro");
    expect(t.indexOf("Black Market")).toBeLessThan(t.indexOf("Caerleon"));
    expect(t).toContain("144 k");
  });

  it("un dato viejo no se presenta como mejor precio y se avisa", async () => {
    const api = apiFalsa({ obtenerObjeto: async () => ESPADA, comparar: async () => COMPARACIONES });
    const { i, texto } = interaccion({ objeto: "T6_MAIN_SWORD" });
    await precio.ejecutar(i, contexto(api));
    expect(texto()).toMatch(/Thetford.*hace 18 h/);
  });

  it("artefacto: no manda calidad ni encantamiento aunque se escriban", async () => {
    const api = apiFalsa({ obtenerObjeto: async () => ARTEFACTO, comparar: async () => [] });
    const { i } = interaccion({ objeto: ARTEFACTO.base_id, encantamiento: 3, calidad: 5 });
    await precio.ejecutar(i, contexto(api));
    expect(api.comparar).toHaveBeenCalledWith(expect.objectContaining({ encantamiento: 0, calidad: 1 }));
  });

  it("sin datos de mercado lo dice", async () => {
    const api = apiFalsa({ obtenerObjeto: async () => ESPADA, comparar: async () => [] });
    const { i, texto } = interaccion({ objeto: "T6_MAIN_SWORD" });
    await precio.ejecutar(i, contexto(api));
    expect(texto()).toContain("No hay precios");
  });

  it("un recurso encantado usa su encantamiento fijo", async () => {
    const mineral = { ...ARTEFACTO, base_id: "T4_ORE_LEVEL2", categoria: "recurso" as const, encantamiento_min: 2, encantamiento_max: 2 };
    const api = apiFalsa({ obtenerObjeto: async () => mineral, comparar: async () => [] });
    const { i } = interaccion({ objeto: "T4_ORE_LEVEL2", encantamiento: 0 });
    await precio.ejecutar(i, contexto(api));
    expect(api.comparar).toHaveBeenCalledWith(expect.objectContaining({ encantamiento: 2, calidad: 1 }));
  });
});

describe("/comparar", () => {
  it("muestra directa y orden por ciudad, la diferencia, y usa la cantidad", async () => {
    const api = apiFalsa({ obtenerObjeto: async () => ESPADA, comparar: async () => COMPARACIONES });
    const { i, texto } = interaccion({ objeto: "T6_MAIN_SWORD", cantidad: 5 });
    await comparar.ejecutar(i, contexto(api));
    expect(api.comparar).toHaveBeenCalledWith(expect.objectContaining({ cantidad: 5 }));
    const t = texto();
    expect(t).toContain("Directa");
    expect(t).toContain("Orden");
    expect(t).toContain("+7.1 k"); // 93 500 - 86 400 en Fort Sterling
    expect(t).toContain("Black Market");
  });
});

describe("/balance", () => {
  it("junta saldo actual, ventas, gastos y resultado", async () => {
    const api = apiFalsa({
      saldoInicial: async () => ({ monto: 120_000_000, fecha: "2026-11-25" }),
      evolucion: async () => [
        { fecha: "2026-11-24", ingresos: 1, gastos: 1, saldo: 119_000_000 },
        { fecha: "2026-11-25", ingresos: 2, gastos: 1, saldo: 120_553_500 },
      ],
      reportes: async () => ({ ...SIN_REPORTE, ventas_netas: 2_000_000, gastos_totales: 450_000, resultado: 1_550_000 }),
    });
    const { i, texto, llamadas } = interaccion();
    await balance.ejecutar(i, contexto(api));
    expect(llamadas[0]?.opciones).toEqual({ flags: EFIMERO });
    expect(texto()).toContain("120.6 M");
    expect(texto()).toContain("+1.6 M");
  });

  it("sin saldo inicial explica cómo configurarlo, sin romperse", async () => {
    const api = apiFalsa({ saldoInicial: async () => null, evolucion: async () => [], reportes: async () => SIN_REPORTE });
    const { i, texto } = interaccion();
    await balance.ejecutar(i, contexto(api));
    expect(texto()).toContain("saldo inicial");
  });
});

describe("/venta", () => {
  const opciones = { objeto: "T6_MAIN_SWORD", ciudad: "Fort Sterling", tipo: "orden", cantidad: 1, precio: 100_000, encantamiento: 2, calidad: 4 };

  it("registra, confirma en privado y anuncia la venta al canal", async () => {
    const api = apiFalsa({ registrarVenta: async () => VENTA });
    const { i, llamadas, texto, publicas } = interaccion(opciones);
    await venta.ejecutar(i, contexto(api));
    expect(api.registrarVenta).toHaveBeenCalledWith({
      base_id: "T6_MAIN_SWORD", encantamiento: 2, calidad: 4, ciudad: "Fort Sterling", tipo: "orden", cantidad: 1, precio_unitario: 100_000,
    });
    expect(llamadas[0]?.opciones).toEqual({ flags: EFIMERO });
    expect(llamadas.filter((l) => l.tipo === "edit")).toHaveLength(1);
    expect(publicas()).toHaveLength(1);
    expect(texto()).toContain("93.5 k");
    expect(JSON.stringify(publicas())).toContain("Julio");
  });

  it("si la API la rechaza (no es admin) solo lo sabe quien la usó", async () => {
    const api = apiFalsa({ registrarVenta: async () => { throw new ErrorApi(403, "Solo un administrador puede registrar"); } });
    const { i, texto, publicas } = interaccion(opciones);
    i.commandName = "venta";
    await despachar(i, { como: () => api }); // el despachador convierte el error en un aviso privado
    expect(publicas()).toHaveLength(0);
    expect(texto()).toContain("Solo un administrador puede registrar");
  });
});

describe("/gasto", () => {
  it("registra el gasto y lo anuncia", async () => {
    const api = apiFalsa({ registrarGasto: async (g) => ({ id: 1, fecha: "2026-11-25T12:00:00Z", ...g }) });
    const { i, publicas, texto } = interaccion({ categoria: "reparaciones", monto: 250_000, descripcion: "Set de caerleon" });
    await gasto.ejecutar(i, contexto(api));
    expect(api.registrarGasto).toHaveBeenCalledWith({ categoria: "reparaciones", monto: 250_000, descripcion: "Set de caerleon" });
    expect(publicas()).toHaveLength(1);
    expect(texto()).toContain("Reparaciones");
    expect(texto()).toContain("250 k");
  });

  it("la descripción es opcional", async () => {
    const api = apiFalsa({ registrarGasto: async (g) => ({ id: 1, fecha: "x", ...g }) });
    const { i } = interaccion({ categoria: "otros", monto: 10 });
    await gasto.ejecutar(i, contexto(api));
    expect(api.registrarGasto).toHaveBeenCalledWith({ categoria: "otros", monto: 10, descripcion: "" });
  });
});
