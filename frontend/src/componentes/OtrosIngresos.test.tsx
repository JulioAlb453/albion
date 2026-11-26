import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Ingreso } from "../api/tipos";
import { instalarApi, montarPagina, USUARIO_GENERAL } from "../pruebas/utiles";
import { OtrosIngresos } from "./OtrosIngresos";

const INGRESOS: Ingreso[] = [
  { id: 1, categoria: "donacion", descripcion: "Ana", monto: 2_000_000, fecha: "2026-11-24T10:00:00Z" },
  { id: 2, categoria: "territorios", descripcion: "", monto: 500_000, fecha: "2026-11-25T10:00:00Z" },
];

describe("OtrosIngresos", () => {
  it("lista lo más reciente arriba, con su categoría y el total", async () => {
    instalarApi({ "GET /api/ingresos": INGRESOS });
    montarPagina(<OtrosIngresos />);
    const [, primero, segundo, totales] = within(await screen.findByRole("table")).getAllByRole("row");
    expect(within(primero!).getByText("Territorios y temporada")).toBeInTheDocument();
    expect(within(segundo!).getByText("Donación")).toBeInTheDocument();
    expect(within(totales!).getByTitle("2,500,000")).toBeInTheDocument();
  });

  it("el admin registra un ingreso", async () => {
    const llamadas = instalarApi({ "GET /api/ingresos": [], "POST /api/ingresos": INGRESOS[0]! });
    montarPagina(<OtrosIngresos />);
    expect(await screen.findByText(/todavía no hay otros ingresos/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /registrar ingreso/i }));
    const dialogo = screen.getByRole("dialog", { name: /registrar ingreso/i });
    await userEvent.selectOptions(within(dialogo).getByLabelText(/categoría/i), "donacion");
    await userEvent.type(within(dialogo).getByLabelText(/monto/i), "2000000");
    await userEvent.type(within(dialogo).getByLabelText(/descripción/i), "Ana");
    await userEvent.click(within(dialogo).getByRole("button", { name: /guardar/i }));
    await waitFor(() => expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toEqual({
      categoria: "donacion", descripcion: "Ana", monto: 2_000_000,
    }));
    expect(await screen.findByText(/ingreso registrado/i)).toBeInTheDocument();
  });

  it("un general no registra ni elimina", async () => {
    instalarApi({ "GET /api/ingresos": INGRESOS });
    montarPagina(<OtrosIngresos />, { usuario: USUARIO_GENERAL });
    await screen.findByRole("table");
    expect(screen.queryByRole("button", { name: /registrar ingreso|eliminar/i })).not.toBeInTheDocument();
  });
});
