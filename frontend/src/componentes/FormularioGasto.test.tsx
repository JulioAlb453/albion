import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { instalarApi, json, montarPagina } from "../pruebas/utiles";
import { FormularioGasto } from "./FormularioGasto";

function montar(rutas: Record<string, unknown> = {}) {
  const llamadas = instalarApi({
    "POST /api/gastos": { id: 1, categoria: "reparaciones", descripcion: "ZvZ", monto: 500_000, fecha: "2026-11-25T12:00:00Z" },
    ...rutas,
  });
  const alTerminar = vi.fn();
  montarPagina(<FormularioGasto alTerminar={alTerminar} />);
  return { llamadas, alTerminar };
}
const guardar = () => screen.getByRole("button", { name: /guardar gasto/i });

describe("FormularioGasto", () => {
  it("no deja guardar sin monto", () => {
    montar();
    expect(guardar()).toBeDisabled();
  });

  it("ofrece las categorías de gasto del gremio", () => {
    montar();
    const opciones = Array.from(screen.getByLabelText(/categoría/i).querySelectorAll("option")).map((o) => o.textContent);
    expect(opciones).toEqual([
      "Compra de equipo", "Reparaciones", "Reequipamiento de builds", "Ingredientes de comida", "Otros",
    ]);
  });

  it("guarda con la categoría, la descripción y el monto, avisa y cierra", async () => {
    const { llamadas, alTerminar } = montar();
    await userEvent.selectOptions(screen.getByLabelText(/categoría/i), "reparaciones");
    await userEvent.type(screen.getByLabelText(/descripción/i), "ZvZ");
    await userEvent.type(screen.getByLabelText(/monto/i), "500000");
    await userEvent.click(guardar());
    await waitFor(() => expect(alTerminar).toHaveBeenCalledOnce());
    expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toEqual({
      categoria: "reparaciones", descripcion: "ZvZ", monto: 500_000,
    });
    expect(await screen.findByText(/gasto registrado/i)).toBeInTheDocument();
  });

  it("la categoría «Otros» exige una descripción", async () => {
    montar();
    await userEvent.selectOptions(screen.getByLabelText(/categoría/i), "otros");
    await userEvent.type(screen.getByLabelText(/monto/i), "1000");
    expect(guardar()).toBeDisabled();
    expect(screen.getByText(/escribe una descripción/i)).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/descripción/i), "Impuesto de isla");
    expect(guardar()).toBeEnabled();
  });

  it("si el servidor lo rechaza muestra el motivo y no cierra", async () => {
    const { alTerminar } = montar({ "POST /api/gastos": json({ detail: "El monto del gasto debe ser mayor a cero" }, 422) });
    await userEvent.type(screen.getByLabelText(/monto/i), "5");
    await userEvent.click(guardar());
    expect(await screen.findByRole("alert")).toHaveTextContent("El monto del gasto debe ser mayor a cero");
    expect(alTerminar).not.toHaveBeenCalled();
  });
});
