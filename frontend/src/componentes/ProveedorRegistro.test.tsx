import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { instalarApi, montarPagina } from "../pruebas/utiles";
import { useRegistro } from "./ContextoRegistro";
import { ProveedorRegistro } from "./ProveedorRegistro";

function Disparador() {
  const { abrirVenta } = useRegistro();
  return <button onClick={() => abrirVenta({ ciudad: "Lymhurst", precio_unitario: 5_000 })}>abrir</button>;
}

describe("ProveedorRegistro", () => {
  it("abre el formulario con los datos que se le pasan y se cierra con Escape", async () => {
    instalarApi({});
    montarPagina(<ProveedorRegistro><Disparador /></ProveedorRegistro>);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    await userEvent.click(screen.getByText("abrir"));
    expect(screen.getByRole("dialog", { name: /registrar venta/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/ciudad/i)).toHaveValue("Lymhurst");
    expect(screen.getByLabelText(/precio por unidad/i)).toHaveValue(5_000);

    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("cada vez que se abre empieza limpio", async () => {
    instalarApi({});
    montarPagina(<ProveedorRegistro><Disparador /></ProveedorRegistro>);
    await userEvent.click(screen.getByText("abrir"));
    await userEvent.clear(screen.getByLabelText(/precio por unidad/i));
    await userEvent.type(screen.getByLabelText(/precio por unidad/i), "9");
    await userEvent.keyboard("{Escape}");
    await userEvent.click(screen.getByText("abrir"));
    expect(screen.getByLabelText(/precio por unidad/i)).toHaveValue(5_000);
  });
});
