import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Reportes as TipoReportes } from "../api/tipos";
import { OBJETO_ESPADA } from "../pruebas/datos";
import { instalarApi, json, montarPagina, ultimaDescarga } from "../pruebas/utiles";
import { guardarArchivo } from "../util/descargar";
import { diaLocalHaceDias, finDelDia, inicioDelDia } from "../util/formato";
import { Reportes } from "./Reportes";

vi.mock("../util/descargar", () => ({ guardarArchivo: vi.fn() }));

const ARMADURA = { ...OBJETO_ESPADA, base_id: "T6_ARMOR_PLATE_SET1", nombre: "Armadura de soldado del maestro", etiqueta: "T6.0" };
const DATOS: TipoReportes = {
  ganancia_por_objeto: [
    { objeto: OBJETO_ESPADA, unidades: 3, bruto: 300_000, impuesto: 12_000, tarifa_publicacion: 2_500, neto: 285_500 },
    { objeto: ARMADURA, unidades: 1, bruto: 100_000, impuesto: 4_000, tarifa_publicacion: 0, neto: 96_000 },
  ],
  impuestos: { impuesto_venta: 16_000, tarifa_publicacion: 2_500, total: 18_500 },
  gastos_por_categoria: [
    { categoria: "reparaciones", monto: 300_000 },
    { categoria: "compra_equipo", monto: 200_000 },
  ],
  ventas_netas: 381_500,
  gastos_totales: 500_000,
  resultado: -118_500,
};
const RUTAS = { "GET /api/reportes": DATOS };
/** Los bloques aparecen cuando llegan los datos, así que se esperan. */
const bloque = async (titulo: string | RegExp) =>
  within((await screen.findByRole("heading", { name: titulo })).closest("section")!);
const ultima = (llamadas: ReturnType<typeof instalarApi>, ruta = "/api/reportes") => llamadas.filter((l) => l.ruta === ruta).at(-1)!;

describe("resumen", () => {
  it("muestra el resultado del periodo, aunque sea negativo", async () => {
    instalarApi(RUTAS);
    montarPagina(<Reportes />);
    const resultado = await bloque("Resultado del periodo");
    expect(await resultado.findByTitle("-118,500")).toHaveTextContent("-118.5 k");
    expect(resultado.getByText(/381\.5 k de ventas netas/)).toBeInTheDocument();
    expect(resultado.getByText(/500 k de gastos/)).toBeInTheDocument();
  });

  it("dice cuánto se pagó en impuestos y qué parte de lo vendido se fue en ellos", async () => {
    instalarApi(RUTAS);
    montarPagina(<Reportes />);
    const impuestos = await bloque("Impuestos pagados");
    expect(await impuestos.findByTitle("18,500")).toHaveTextContent("18.5 k");
    expect(impuestos.getByText(/4\.6 % de lo vendido/)).toBeInTheDocument();
    expect(impuestos.getByText("Impuesto de venta")).toBeInTheDocument();
    expect(impuestos.getByText("Tarifa de publicación")).toBeInTheDocument();
  });

  it("reparte los gastos por categoría", async () => {
    instalarApi(RUTAS);
    montarPagina(<Reportes />);
    const gastos = await bloque("Gastos por categoría");
    expect(await gastos.findByText("Reparaciones")).toBeInTheDocument();
    expect(gastos.getByText("Compra de equipo")).toBeInTheDocument();
  });

  it("lista la ganancia de cada objeto con unidades, impuestos y neto", async () => {
    instalarApi(RUTAS);
    montarPagina(<Reportes />);
    const filas = within(await screen.findByRole("table")).getAllByRole("row");
    expect(filas).toHaveLength(1 + 2);
    expect(within(filas[1]!).getByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(within(filas[1]!).getByText("3")).toBeInTheDocument();
    expect(within(filas[1]!).getByTitle("285,500")).toBeInTheDocument();
    expect(within(filas[2]!).getByText("Armadura de soldado del maestro")).toBeInTheDocument();
  });

  it("sin ventas en el periodo lo dice", async () => {
    instalarApi({ "GET /api/reportes": { ...DATOS, ganancia_por_objeto: [], impuestos: { impuesto_venta: 0, tarifa_publicacion: 0, total: 0 }, ventas_netas: 0, resultado: -500_000 } });
    montarPagina(<Reportes />);
    expect(await screen.findByText(/sin ventas en este periodo/i)).toBeInTheDocument();
  });

  it("si el reporte falla lo dice y deja reintentar", async () => {
    instalarApi({ "GET /api/reportes": json({ detail: "Falló la base de datos" }, 500) });
    montarPagina(<Reportes />);
    expect(await screen.findByText(/no se pudo cargar el reporte/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeInTheDocument();
  });
});

describe("periodo", () => {
  it("arranca con todo el historial", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Reportes />);
    await screen.findByRole("table");
    expect(ultima(llamadas).params).toEqual({});
    expect(screen.getByRole("button", { name: "Todo" })).toHaveAttribute("aria-pressed", "true");
  });

  it("los atajos piden los últimos días en hora local", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Reportes />);
    await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", { name: "30 días" }));
    await waitFor(() => expect(ultima(llamadas).params).toEqual({ desde: inicioDelDia(diaLocalHaceDias(30)) }));
    expect(screen.getByRole("button", { name: "30 días" })).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(screen.getByRole("button", { name: "Todo" }));
    await waitFor(() => expect(ultima(llamadas).params).toEqual({}));
  });

  it("también se puede elegir un rango a mano", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Reportes />);
    await screen.findByRole("table");
    fireEvent.change(screen.getByLabelText(/desde/i), { target: { value: "2026-11-01" } });
    fireEvent.change(screen.getByLabelText(/hasta/i), { target: { value: "2026-11-15" } });
    await waitFor(() => expect(ultima(llamadas).params).toEqual({ desde: inicioDelDia("2026-11-01"), hasta: finDelDia("2026-11-15") }));
    expect(screen.getByRole("button", { name: "Todo" })).toHaveAttribute("aria-pressed", "false");
  });
});

describe("exportar", () => {
  it("baja el reporte del periodo en Excel (todas las tablas) o en CSV (por objeto)", async () => {
    const archivo = () => new Response("x", { headers: { "content-disposition": 'attachment; filename="reportes-2026-11-25.xlsx"' } });
    const llamadas = instalarApi({ ...RUTAS, "GET /api/reportes/exportar": archivo });
    montarPagina(<Reportes />);
    await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", { name: "30 días" }));
    await userEvent.click(screen.getByRole("button", { name: /exportar excel/i }));
    await waitFor(() => expect(guardarArchivo).toHaveBeenCalled());
    expect(await ultimaDescarga()).toEqual({ nombre: "reportes-2026-11-25.xlsx", contenido: "x" });
    expect(ultima(llamadas, "/api/reportes/exportar").params).toEqual({ desde: inicioDelDia(diaLocalHaceDias(30)), formato: "xlsx" });

    await userEvent.click(screen.getByRole("button", { name: /exportar csv/i }));
    await waitFor(() => expect(ultima(llamadas, "/api/reportes/exportar").params.formato).toBe("csv"));
  });
});
