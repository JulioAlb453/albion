import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Cajon } from "./Cajon";

describe("Cajon", () => {
  it("cerrado no muestra nada", () => {
    render(<Cajon abierto={false} titulo="Registrar venta" alCerrar={() => {}}>contenido</Cajon>);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("abierto es un diálogo con su título y su contenido", () => {
    render(<Cajon abierto titulo="Registrar venta" alCerrar={() => {}}>contenido</Cajon>);
    const dialogo = screen.getByRole("dialog", { name: "Registrar venta" });
    expect(dialogo).toHaveAttribute("aria-modal", "true");
    expect(dialogo).toHaveTextContent("contenido");
  });

  it("se cierra con Escape, con la X y al hacer clic fuera, pero no al hacer clic dentro", async () => {
    const alCerrar = vi.fn();
    render(<Cajon abierto titulo="Registrar venta" alCerrar={alCerrar}>contenido</Cajon>);

    await userEvent.click(screen.getByText("contenido"));
    expect(alCerrar).not.toHaveBeenCalled();

    await userEvent.keyboard("{Escape}");
    await userEvent.click(screen.getByRole("button", { name: /cerrar/i }));
    await userEvent.click(screen.getByTestId("cajon-fondo"));
    expect(alCerrar).toHaveBeenCalledTimes(3);
  });

  it("pone el foco dentro al abrir", () => {
    render(<Cajon abierto titulo="Registrar venta" alCerrar={() => {}}><input aria-label="Precio" /></Cajon>);
    expect(screen.getByRole("dialog")).toContainElement(document.activeElement as HTMLElement);
  });
});
