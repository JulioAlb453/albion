import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { PagoSemanal } from "../api/tipos";
import { instalarApi, montarPagina, USUARIO_GENERAL } from "../pruebas/utiles";
import { PagosSemanales } from "./PagosSemanales";

const pago = (cambios: Partial<PagoSemanal>): PagoSemanal => ({
  id: 1, miembro: "Ana", monto: 1_000_000, descripcion: "", semana: "2026-11-23", fin_semana: "2026-11-29",
  pagado: 0, fecha_pago: null, estado: "pendiente", no_reclamado: 0, ...cambios,
});
const PAGOS = [
  pago({ id: 1, miembro: "Ana" }),
  pago({ id: 2, miembro: "Beto", pagado: 400_000, fecha_pago: "2026-11-24T18:00:00Z", estado: "parcial" }),
  pago({ id: 3, miembro: "Caro", pagado: 1_000_000, fecha_pago: "2026-11-25T10:00:00Z", estado: "pagado" }),
];
const HOY = new Date("2026-11-25T12:00:00Z");

beforeEach(() => {
  vi.useFakeTimers({ now: HOY, toFake: ["Date"] });
});
afterEach(() => vi.useRealTimers());

const llamadasA = (llamadas: ReturnType<typeof instalarApi>, metodo: string) => llamadas.filter((l) => l.metodo === metodo);

describe("PagosSemanales", () => {
  it("muestra la semana actual con cada miembro, lo asignado, lo pagado y su estado", async () => {
    const llamadas = instalarApi({ "GET /api/pagos-semanales": PAGOS });
    montarPagina(<PagosSemanales />);
    expect(screen.getByText("23 nov – 29 nov")).toBeInTheDocument();
    const tabla = await screen.findByRole("table");
    expect(llamadasA(llamadas, "GET").at(-1)?.params).toEqual({ semana: "2026-11-23" });
    const [, ana, beto, caro, totales] = within(tabla).getAllByRole("row");
    expect(within(ana!).getByText("Pendiente")).toBeInTheDocument();
    expect(within(beto!).getByText("Pago parcial")).toBeInTheDocument();
    expect(within(beto!).getByTitle("400,000")).toBeInTheDocument();
    expect(within(caro!).getByText("Pagado")).toBeInTheDocument();
    expect(within(totales!).getByTitle("3,000,000")).toBeInTheDocument(); // asignado
    expect(within(totales!).getByTitle("1,400,000")).toBeInTheDocument(); // pagado
  });

  it("navega entre semanas", async () => {
    const llamadas = instalarApi({ "GET /api/pagos-semanales": [] });
    montarPagina(<PagosSemanales />);
    await userEvent.click(screen.getByRole("button", { name: /semana anterior/i }));
    expect(screen.getByText("16 nov – 22 nov")).toBeInTheDocument();
    await waitFor(() => expect(llamadasA(llamadas, "GET").at(-1)?.params).toEqual({ semana: "2026-11-16" }));
    expect(await screen.findByText(/no se asignaron pagos/i)).toBeInTheDocument();
  });

  it("una semana terminada dice cuánto quedó para el gremio", async () => {
    instalarApi({
      "GET /api/pagos-semanales": [pago({ semana: "2026-11-16", fin_semana: "2026-11-22", pagado: 400_000, fecha_pago: "2026-11-20T10:00:00Z", estado: "no_reclamado", no_reclamado: 600_000 })],
    });
    montarPagina(<PagosSemanales />);
    await userEvent.click(screen.getByRole("button", { name: /semana anterior/i }));
    expect(await screen.findByText("No reclamado")).toBeInTheDocument();
    expect(screen.getByText(/queda para el gremio/i).closest("p")).toHaveTextContent("600 k");
  });

  it("el admin asigna un pago en la semana que está viendo", async () => {
    const llamadas = instalarApi({ "GET /api/pagos-semanales": [], "POST /api/pagos-semanales": pago({}) });
    montarPagina(<PagosSemanales />);
    await userEvent.click(screen.getByRole("button", { name: /asignar pago/i }));
    const dialogo = screen.getByRole("dialog", { name: /asignar pago/i });
    await userEvent.type(within(dialogo).getByLabelText(/miembro/i), "  Ana ");
    await userEvent.type(within(dialogo).getByLabelText(/monto/i), "1000000");
    await userEvent.click(within(dialogo).getByRole("button", { name: /guardar/i }));
    await waitFor(() => expect(llamadasA(llamadas, "POST")[0]?.cuerpo).toEqual({ miembro: "Ana", monto: 1_000_000, semana: "2026-11-23", descripcion: "" }));
    expect(await screen.findByText(/pago asignado/i)).toBeInTheDocument();
  });

  it("el admin registra un pago parcial y luego lo corrige", async () => {
    const llamadas = instalarApi({
      "GET /api/pagos-semanales": PAGOS,
      "PATCH /api/pagos-semanales/2": pago({ id: 2, miembro: "Beto", pagado: 1_000_000, estado: "pagado" }),
    });
    montarPagina(<PagosSemanales />);
    await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", { name: /registrar pago de beto/i }));
    const dialogo = screen.getByRole("dialog", { name: /registrar pago/i });
    const pagado = within(dialogo).getByLabelText(/total pagado/i);
    expect(pagado).toHaveValue(400_000); // empieza con lo ya pagado, para corregirlo
    expect(within(dialogo).getByText(/entre el 23 nov y el 29 nov/i)).toBeInTheDocument();
    await userEvent.click(within(dialogo).getByRole("button", { name: /pago completo/i }));
    expect(pagado).toHaveValue(1_000_000);
    await userEvent.click(within(dialogo).getByRole("button", { name: /guardar/i }));
    await waitFor(() => expect(llamadasA(llamadas, "PATCH")[0]?.cuerpo).toEqual({ pagado: 1_000_000 }));
    expect(await screen.findByText(/pago registrado/i)).toBeInTheDocument();
  });

  it("no deja pagar más de lo asignado", async () => {
    instalarApi({ "GET /api/pagos-semanales": PAGOS });
    montarPagina(<PagosSemanales />);
    await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", { name: /registrar pago de ana/i }));
    const dialogo = screen.getByRole("dialog", { name: /registrar pago/i });
    await userEvent.type(within(dialogo).getByLabelText(/total pagado/i), "1000001");
    expect(within(dialogo).getByText(/no puede pasar de lo asignado/i)).toBeInTheDocument();
    expect(within(dialogo).getByRole("button", { name: /guardar/i })).toBeDisabled();
  });

  it("un general solo consulta", async () => {
    instalarApi({ "GET /api/pagos-semanales": PAGOS });
    montarPagina(<PagosSemanales />, { usuario: USUARIO_GENERAL });
    await screen.findByRole("table");
    expect(screen.queryByRole("button", { name: /asignar pago|registrar pago|eliminar/i })).not.toBeInTheDocument();
  });
});
