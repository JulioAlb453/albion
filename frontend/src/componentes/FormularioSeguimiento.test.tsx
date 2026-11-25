import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ESPADA } from "../pruebas/datos";
import { instalarApi, json, montarPagina } from "../pruebas/utiles";
import { FormularioSeguimiento } from "./FormularioSeguimiento";

function montar(rutas: Record<string, unknown> = {}, prefill = { objeto: ESPADA, encantamiento: 2, calidad: 4 }) {
  const llamadas = instalarApi({
    "POST /api/seguimientos": { id: 1, objeto: { base_id: "T6_MAIN_SWORD", nombre: "Espada ancha del maestro", etiqueta: "T6.2", encantamiento: 2, calidad: 4 }, ciudad_referencia: "Fort Sterling", porcentaje_minimo: 15, neto_minimo: null },
    ...rutas,
  });
  const alTerminar = vi.fn();
  montarPagina(<FormularioSeguimiento prefill={prefill} alTerminar={alTerminar} />);
  return { llamadas, alTerminar };
}
const guardar = () => screen.getByRole("button", { name: /vigilar objeto/i });
const cuerpo = (llamadas: ReturnType<typeof instalarApi>) => llamadas.find((l) => l.metodo === "POST")?.cuerpo;

describe("FormularioSeguimiento", () => {
  it("necesita al menos un criterio para poder guardar", async () => {
    montar();
    expect(guardar()).toBeDisabled();
    await userEvent.type(screen.getByLabelText(/% más neto/i), "15");
    expect(guardar()).toBeEnabled();
  });

  it("vigila con un porcentaje sobre la ciudad de referencia", async () => {
    const { llamadas, alTerminar } = montar();
    await userEvent.type(screen.getByLabelText(/% más neto/i), "15");
    await userEvent.click(guardar());
    await waitFor(() => expect(alTerminar).toHaveBeenCalledOnce());
    expect(cuerpo(llamadas)).toEqual({
      base_id: "T6_MAIN_SWORD", encantamiento: 2, calidad: 4, ciudad_referencia: "Fort Sterling", porcentaje_minimo: 15,
    });
    expect(await screen.findByText(/ahora vigilas/i)).toBeInTheDocument();
  });

  it("acepta decimales y los dos criterios a la vez", async () => {
    const { llamadas, alTerminar } = montar();
    await userEvent.selectOptions(screen.getByLabelText(/ciudad de referencia/i), "Lymhurst");
    await userEvent.type(screen.getByLabelText(/% más neto/i), "12.5");
    await userEvent.type(screen.getByLabelText(/llega a/i), "300000");
    await userEvent.click(guardar());
    await waitFor(() => expect(alTerminar).toHaveBeenCalled());
    expect(cuerpo(llamadas)).toMatchObject({ ciudad_referencia: "Lymhurst", porcentaje_minimo: 12.5, neto_minimo: 300_000 });
  });

  it("si el servidor lo rechaza muestra el motivo y no cierra", async () => {
    const { alTerminar } = montar({ "POST /api/seguimientos": json({ detail: "El seguimiento necesita al menos un criterio de alerta" }, 422) });
    await userEvent.type(screen.getByLabelText(/llega a/i), "5");
    await userEvent.click(guardar());
    expect(await screen.findByRole("alert")).toHaveTextContent(/al menos un criterio/i);
    expect(alTerminar).not.toHaveBeenCalled();
  });

  it("sin objeto no se puede guardar aunque haya criterio", async () => {
    montar({}, {} as never);
    await userEvent.type(screen.getByLabelText(/% más neto/i), "15");
    expect(guardar()).toBeDisabled();
  });
});
