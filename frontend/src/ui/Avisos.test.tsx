import { act, fireEvent, render, screen } from "@testing-library/react";
import { ProveedorAvisos, useAvisos } from "./Avisos";

function Boton({ tipo }: { tipo?: "exito" | "error" }) {
  const { avisar } = useAvisos();
  return <button onClick={() => avisar("Venta guardada", tipo)}>guardar</button>;
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("avisos", () => {
  it("muestra el aviso y lo quita solo pasados unos segundos", () => {
    render(<ProveedorAvisos><Boton /></ProveedorAvisos>);
    fireEvent.click(screen.getByText("guardar"));
    expect(screen.getByText("Venta guardada")).toBeInTheDocument();
    act(() => void vi.advanceTimersByTime(6_000));
    expect(screen.queryByText("Venta guardada")).not.toBeInTheDocument();
  });

  it("los errores se anuncian como alerta y los éxitos como estado", () => {
    render(<ProveedorAvisos><Boton tipo="error" /></ProveedorAvisos>);
    fireEvent.click(screen.getByText("guardar"));
    expect(screen.getByRole("alert")).toHaveTextContent("Venta guardada");
  });

  it("se puede cerrar a mano", () => {
    render(<ProveedorAvisos><Boton tipo="exito" /></ProveedorAvisos>);
    fireEvent.click(screen.getByText("guardar"));
    fireEvent.click(screen.getByRole("button", { name: /cerrar aviso/i }));
    expect(screen.queryByText("Venta guardada")).not.toBeInTheDocument();
  });

  it("varios avisos conviven", () => {
    render(<ProveedorAvisos><Boton /></ProveedorAvisos>);
    fireEvent.click(screen.getByText("guardar"));
    fireEvent.click(screen.getByText("guardar"));
    expect(screen.getAllByText("Venta guardada")).toHaveLength(2);
  });
});
