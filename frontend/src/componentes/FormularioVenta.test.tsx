import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { PrefillVenta } from "./ContextoRegistro";
import { ARTEFACTO, ESPADA, venta } from "../pruebas/datos";
import { instalarApi, json, montarPagina } from "../pruebas/utiles";
import { FormularioVenta } from "./FormularioVenta";

const PREFILL: PrefillVenta = {
  objeto: ESPADA, encantamiento: 2, calidad: 4, cantidad: 1,
  ciudad: "Fort Sterling", tipo: "orden", precio_unitario: 100_000,
};
const vistaPrevia = () => within(screen.getByRole("group", { name: /vista previa/i }));

function montar(prefill?: PrefillVenta, rutas: Record<string, unknown> = {}) {
  const llamadas = instalarApi({ "POST /api/ventas": venta(), ...rutas });
  const alTerminar = vi.fn();
  montarPagina(<FormularioVenta prefill={prefill} alTerminar={alTerminar} />);
  return { llamadas, alTerminar };
}

describe("FormularioVenta", () => {
  it("con datos precargados muestra el objeto y calcula el desglose antes de guardar", () => {
    montar(PREFILL);
    expect(screen.getByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(vistaPrevia().getByText("100,000")).toBeInTheDocument();  // bruto
    expect(vistaPrevia().getByText("4,000")).toBeInTheDocument();    // impuesto
    expect(vistaPrevia().getByText("2,500")).toBeInTheDocument();    // tarifa de publicación
    expect(vistaPrevia().getByText("93,500")).toBeInTheDocument();   // neto
  });

  it("una venta directa no tiene tarifa de publicación", async () => {
    montar(PREFILL);
    await userEvent.click(screen.getByRole("radio", { name: /venta directa/i }));
    expect(vistaPrevia().getByText("96,000")).toBeInTheDocument();
    expect(vistaPrevia().queryByText(/tarifa de publicación/i)).not.toBeInTheDocument();
  });

  it("el Black Market solo admite venta directa", async () => {
    montar(PREFILL);
    await userEvent.selectOptions(screen.getByLabelText(/ciudad/i), "Black Market");
    expect(screen.getByRole("radio", { name: /orden de venta/i })).toBeDisabled();
    expect(screen.getByRole("radio", { name: /venta directa/i })).toBeChecked();
  });

  it("un artefacto no tiene encantamiento ni calidad", () => {
    montar({ objeto: ARTEFACTO });
    expect(screen.queryByLabelText(/encantamiento/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/calidad/i)).not.toBeInTheDocument();
  });

  it("la tarifa por reajustes solo existe en las órdenes y suma al desglose", async () => {
    montar(PREFILL);
    await userEvent.type(screen.getByLabelText(/reajustes/i), "1000");
    expect(vistaPrevia().getByText("3,500")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("radio", { name: /venta directa/i }));
    expect(screen.queryByLabelText(/reajustes/i)).not.toBeInTheDocument();
  });

  it("no deja guardar sin objeto ni precio", () => {
    montar();
    expect(screen.getByRole("button", { name: /guardar venta/i })).toBeDisabled();
  });

  it("guarda con lo escrito, avisa y cierra", async () => {
    const { llamadas, alTerminar } = montar(PREFILL);
    await userEvent.click(screen.getByRole("button", { name: /guardar venta/i }));
    await waitFor(() => expect(alTerminar).toHaveBeenCalledOnce());
    expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toEqual({
      base_id: "T6_MAIN_SWORD", encantamiento: 2, calidad: 4, ciudad: "Fort Sterling",
      tipo: "orden", cantidad: 1, precio_unitario: 100_000,
    });
    expect(await screen.findByText(/venta registrada/i)).toBeInTheDocument();
  });

  it("envía la tarifa por reajustes cuando la hay", async () => {
    const { llamadas, alTerminar } = montar(PREFILL);
    await userEvent.type(screen.getByLabelText(/reajustes/i), "1500");
    await userEvent.click(screen.getByRole("button", { name: /guardar venta/i }));
    await waitFor(() => expect(alTerminar).toHaveBeenCalled());
    expect(llamadas.find((l) => l.metodo === "POST")?.cuerpo).toMatchObject({ tarifa_extra: 1500 });
  });

  it("si el servidor rechaza la venta muestra el motivo y no cierra", async () => {
    const { alTerminar } = montar(PREFILL, {
      "POST /api/ventas": json({ detail: "Black Market no admite órdenes de venta" }, 422),
    });
    await userEvent.click(screen.getByRole("button", { name: /guardar venta/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Black Market no admite órdenes de venta");
    expect(alTerminar).not.toHaveBeenCalled();
  });
});
