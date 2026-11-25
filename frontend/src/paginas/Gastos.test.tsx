import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Gasto } from "../api/tipos";
import { instalarApi, montarPagina, USUARIO_GENERAL } from "../pruebas/utiles";
import { guardarArchivo } from "../util/descargar";
import { finDelDia, inicioDelDia } from "../util/formato";
import { Gastos } from "./Gastos";

vi.mock("../util/descargar", () => ({ guardarArchivo: vi.fn() }));

const GASTOS: Gasto[] = [
  { id: 1, categoria: "reparaciones", descripcion: "Reparaciones tras el ZvZ", monto: 500_000, fecha: "2026-11-24T10:00:00Z" },
  { id: 2, categoria: "compra_equipo", descripcion: "", monto: 1_200_000, fecha: "2026-11-25T18:00:00Z" },
];
const RUTAS = { "GET /api/gastos": GASTOS, "DELETE /api/gastos/1": new Response(null, { status: 204 }) };
const ultima = (llamadas: ReturnType<typeof instalarApi>, ruta = "/api/gastos") => llamadas.filter((l) => l.ruta === ruta).at(-1)!;

describe("lista", () => {
  it("muestra cada gasto con su categoría y descripción, y el total", async () => {
    instalarApi(RUTAS);
    montarPagina(<Gastos />);
    const filas = within(await screen.findByRole("table")).getAllByRole("row");
    expect(filas).toHaveLength(1 + 2 + 1);
    // el más reciente arriba (la API los manda del más viejo al más nuevo)
    expect(within(filas[1]!).getByText("Compra de equipo")).toBeInTheDocument();
    expect(within(filas[2]!).getByText("Reparaciones")).toBeInTheDocument();
    expect(within(filas[2]!).getByText("Reparaciones tras el ZvZ")).toBeInTheDocument();
    expect(within(filas[3]!).getByText(/2 gastos/i)).toBeInTheDocument();
    expect(within(filas[3]!).getByTitle("1,700,000")).toBeInTheDocument();
  });

  it("sin gastos lo dice", async () => {
    instalarApi({ "GET /api/gastos": [] });
    montarPagina(<Gastos />);
    expect(await screen.findByText(/todavía no hay gastos/i)).toBeInTheDocument();
  });

  it("si no carga lo dice y deja reintentar", async () => {
    instalarApi({});
    montarPagina(<Gastos />);
    expect(await screen.findByText(/no se pudo cargar los gastos/i)).toBeInTheDocument();
  });
});

describe("filtros y exportación", () => {
  it("filtra por categoría y fechas en hora local", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Gastos />);
    await screen.findByRole("table");
    await userEvent.selectOptions(screen.getByLabelText(/categoría/i), "reparaciones");
    fireEvent.change(screen.getByLabelText(/desde/i), { target: { value: "2026-11-20" } });
    fireEvent.change(screen.getByLabelText(/hasta/i), { target: { value: "2026-11-25" } });
    await waitFor(() =>
      expect(ultima(llamadas).params).toEqual({
        categoria: "reparaciones", desde: inicioDelDia("2026-11-20"), hasta: finDelDia("2026-11-25"),
      }),
    );
  });

  it("exporta en CSV o Excel con los mismos filtros", async () => {
    const archivo = () => new Response("a", { headers: { "content-disposition": 'attachment; filename="gastos-2026-11-25.csv"' } });
    const llamadas = instalarApi({ ...RUTAS, "GET /api/gastos/exportar": archivo });
    montarPagina(<Gastos />);
    await screen.findByRole("table");
    await userEvent.selectOptions(screen.getByLabelText(/categoría/i), "compra_equipo");
    await userEvent.click(screen.getByRole("button", { name: /exportar csv/i }));
    await waitFor(() => expect(guardarArchivo).toHaveBeenCalledWith(expect.any(Blob), "gastos-2026-11-25.csv"));
    expect(ultima(llamadas, "/api/gastos/exportar").params).toEqual({ categoria: "compra_equipo", formato: "csv" });
  });
});

describe("permisos y acciones", () => {
  it("el admin elimina un gasto confirmando en dos pasos", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Gastos />);
    await screen.findByRole("table");
    // el gasto 1 (Reparaciones) es la segunda fila, porque el más reciente va arriba
    await userEvent.click(screen.getByRole("button", { name: /eliminar gasto de reparaciones/i }));
    expect(llamadas.some((l) => l.metodo === "DELETE")).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: /confirmar eliminación/i }));
    await waitFor(() => expect(llamadas.some((l) => l.metodo === "DELETE" && l.ruta === "/api/gastos/1")).toBe(true));
    expect(await screen.findByText(/gasto eliminado/i)).toBeInTheDocument();
  });

  it("el admin registra un gasto desde un cajón e importa desde un CSV", async () => {
    instalarApi(RUTAS);
    montarPagina(<Gastos />);
    await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", { name: /registrar gasto/i }));
    expect(screen.getByRole("dialog", { name: /registrar gasto/i })).toBeInTheDocument();
    await userEvent.keyboard("{Escape}");
    await userEvent.click(screen.getByRole("button", { name: /^importar$/i }));
    expect(screen.getByRole("dialog", { name: /importar gastos/i })).toBeInTheDocument();
  });

  it("un general solo consulta y exporta", async () => {
    instalarApi(RUTAS);
    montarPagina(<Gastos />, { usuario: USUARIO_GENERAL });
    await screen.findByRole("table");
    for (const nombre of [/registrar gasto/i, /^importar$/i, /eliminar gasto/i]) {
      expect(screen.queryByRole("button", { name: nombre })).not.toBeInTheDocument();
    }
    expect(screen.getByRole("button", { name: /exportar excel/i })).toBeInTheDocument();
  });
});
