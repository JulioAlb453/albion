import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Alerta, Reportes, Seguimiento } from "../api/tipos";
import { comparacion, OBJETO_ESPADA, opcion, venta } from "../pruebas/datos";
import { instalarApi, json, montarPagina, USUARIO_GENERAL } from "../pruebas/utiles";
import { Panel } from "./Panel";

const SALDO = { monto: 120_000_000, fecha: "2026-11-05" };
const EVOLUCION = [
  { fecha: "2026-11-24", ingresos: 300_000, gastos: 0, saldo: 120_300_000 },
  { fecha: "2026-11-25", ingresos: 253_500, gastos: 0, saldo: 120_553_500 },
];
const REPORTES: Reportes = {
  ganancia_por_objeto: [],
  impuestos: { impuesto_venta: 44_000, tarifa_publicacion: 2_500, total: 46_500 },
  gastos_por_categoria: [
    { categoria: "reparaciones", monto: 300_000 },
    { categoria: "compra_equipo", monto: 200_000 },
  ],
  ventas_netas: 1_053_500,
  gastos_totales: 500_000,
  ingresos_extra: 0,
  ingresos_por_categoria: [],
  pagos_semanales: 0,
  resultado: 553_500,
};
const ARMADURA = { ...OBJETO_ESPADA, base_id: "T6_ARMOR_PLATE_SET1", nombre: "Armadura de soldado del maestro", etiqueta: "T6.0" };
const VENTAS = [
  venta({ id: 1, fecha: "2026-11-24T10:00:00Z" }),
  venta({ id: 2, objeto: ARMADURA, fecha: "2026-11-25T18:00:00Z" }),
];
const SEGUIMIENTO: Seguimiento = {
  id: 1, objeto: OBJETO_ESPADA, ciudad_referencia: "Fort Sterling", porcentaje_minimo: 15, neto_minimo: null,
};
const ALERTA: Alerta = {
  id: 1, seguimiento_id: 1, objeto: OBJETO_ESPADA, ciudad: "Black Market", tipo: "directa",
  neto_unitario: 144_000, neto_referencia: 93_500,
  motivo: "Black Market paga 54.0% más neto que Fort Sterling", fecha: "2026-11-25T12:00:00Z",
};
const COMPARACIONES = [
  comparacion("Black Market", { directa: opcion("directa", 144_000) }),
  comparacion("Fort Sterling", { directa: opcion("directa", 86_400), orden: opcion("orden", 93_500) }),
];
const RUTAS = {
  "GET /api/balance/saldo-inicial": SALDO,
  "GET /api/balance/evolucion": EVOLUCION,
  "GET /api/reportes": REPORTES,
  "GET /api/ventas": VENTAS,
  "GET /api/seguimientos": [SEGUIMIENTO],
  "GET /api/alertas": [ALERTA],
  "GET /api/mercado/comparar": COMPARACIONES,
};
const bloque = (titulo: string | RegExp) => within(screen.getByRole("heading", { name: titulo }).closest("section")!);

describe("saldo", () => {
  it("muestra el saldo actual y cuánto cambió desde el saldo inicial", async () => {
    instalarApi(RUTAS);
    montarPagina(<Panel />);
    expect(await screen.findByTitle("120,553,500")).toHaveTextContent("120.6 M");
    expect(screen.getByText(/\+553\.5 k/)).toBeInTheDocument();
  });

  it("sin saldo inicial, el admin ve cómo configurarlo y lo guarda", async () => {
    const llamadas = instalarApi({
      ...RUTAS,
      "GET /api/balance/saldo-inicial": json({ detail: "Falta configurar el saldo inicial" }, 404),
      "GET /api/balance/evolucion": json({ detail: "Falta configurar el saldo inicial" }, 404),
      "PUT /api/balance/saldo-inicial": (llamada: { cuerpo: unknown }) => llamada.cuerpo,
    });
    montarPagina(<Panel />);
    expect(await screen.findByText(/configura tu saldo inicial/i)).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/monto/i), "120000000");
    fireEvent.change(screen.getByLabelText(/fecha/i), { target: { value: "2026-11-05" } });
    await userEvent.click(screen.getByRole("button", { name: /guardar/i }));

    await waitFor(() => expect(llamadas.some((l) => l.metodo === "PUT")).toBe(true));
    expect(llamadas.find((l) => l.metodo === "PUT")?.cuerpo).toEqual({ monto: 120_000_000, fecha: "2026-11-05" });
  });

  it("sin saldo inicial, un general solo ve que falta", async () => {
    instalarApi({
      ...RUTAS,
      "GET /api/balance/saldo-inicial": json({ detail: "x" }, 404),
      "GET /api/balance/evolucion": json({ detail: "x" }, 404),
    });
    montarPagina(<Panel />, { usuario: USUARIO_GENERAL });
    expect(await screen.findByText(/todavía no se configuró el saldo inicial/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /guardar/i })).not.toBeInTheDocument();
  });
});

describe("resumen del periodo", () => {
  it("muestra ventas netas, gastos, resultado e impuestos pagados", async () => {
    instalarApi(RUTAS);
    montarPagina(<Panel />);
    await screen.findByTitle("1,053,500");
    const resumen = bloque("Resumen del periodo");
    expect(resumen.getByText("Ventas netas")).toBeInTheDocument();
    expect(resumen.getByTitle("1,053,500")).toHaveTextContent("1.1 M");
    expect(resumen.getByTitle("500,000")).toHaveTextContent("500 k");
    expect(resumen.getByTitle("553,500")).toHaveTextContent("553.5 k");
    expect(resumen.getByTitle("46,500")).toHaveTextContent("46.5 k");
  });

  it("pide el reporte del periodo que se elige", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Panel />);
    await screen.findByTitle("1,053,500");
    const ultimo = () => llamadas.filter((l) => l.ruta === "/api/reportes").at(-1)!;
    expect(ultimo().params.desde).toBeDefined(); // por defecto, los últimos 30 días

    await userEvent.click(screen.getByRole("button", { name: "Todo" }));
    await waitFor(() => expect(ultimo().params.desde).toBeUndefined());

    await userEvent.click(screen.getByRole("button", { name: "7 días" }));
    await waitFor(() => expect(ultimo().params.desde).toBeDefined());
    expect(screen.getByRole("button", { name: "7 días" })).toHaveAttribute("aria-pressed", "true");
  });

  it("si el reporte falla, lo dice y el resto del panel sigue funcionando", async () => {
    instalarApi({ ...RUTAS, "GET /api/reportes": json({ detail: "Falló la base de datos" }, 500) });
    montarPagina(<Panel />);
    expect(await screen.findByText(/no se pudo cargar el resumen/i)).toBeInTheDocument();
    expect(await screen.findByTitle("120,553,500")).toBeInTheDocument();
  });
});

describe("oportunidades de venta", () => {
  it("para cada objeto vigilado dice dónde conviene vender y cuánto más que en la ciudad de referencia", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Panel />);
    const oportunidades = bloque("Mejores oportunidades");
    expect(await oportunidades.findByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(oportunidades.getByText("Black Market")).toBeInTheDocument();
    expect(oportunidades.getByTitle("144,000")).toHaveTextContent("144 k");
    expect(oportunidades.getByText(/\+54 % sobre Fort Sterling/)).toBeInTheDocument();
    expect(llamadas.find((l) => l.ruta === "/api/mercado/comparar")?.params).toEqual({
      base_id: "T6_MAIN_SWORD", encantamiento: "2", calidad: "4", cantidad: "1",
    });
  });

  it("sin objetos vigilados invita a vigilar uno", async () => {
    instalarApi({ ...RUTAS, "GET /api/seguimientos": [] });
    montarPagina(<Panel />);
    const oportunidades = bloque("Mejores oportunidades");
    expect(await oportunidades.findByText(/todavía no vigilas ningún objeto/i)).toBeInTheDocument();
    expect(oportunidades.getByRole("link", { name: /vigilar un objeto/i })).toHaveAttribute("href", "/alertas");
  });
});

describe("actividad reciente", () => {
  it("lista las últimas ventas, la más reciente primero", async () => {
    instalarApi(RUTAS);
    montarPagina(<Panel />);
    const ultimas = bloque("Últimas ventas");
    expect(await ultimas.findByText("Armadura de soldado del maestro")).toBeInTheDocument();
    const nombres = ultimas.getAllByRole("row").slice(1).map((f) => within(f).getAllByRole("cell")[1]!.textContent);
    expect(nombres[0]).toContain("Armadura de soldado del maestro");
    expect(nombres[1]).toContain("Espada ancha del maestro");
  });

  it("sin ventas dice que todavía no hay", async () => {
    instalarApi({ ...RUTAS, "GET /api/ventas": [] });
    montarPagina(<Panel />);
    expect(await bloque("Últimas ventas").findByText(/todavía no hay ventas/i)).toBeInTheDocument();
  });

  it("muestra las alertas recientes con su motivo", async () => {
    instalarApi(RUTAS);
    montarPagina(<Panel />);
    expect(await bloque("Alertas recientes").findByText(/black market paga 54\.0% más neto/i)).toBeInTheDocument();
  });
});
