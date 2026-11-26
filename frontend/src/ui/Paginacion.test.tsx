import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { numerosDePagina, Paginacion } from "./Paginacion";

describe("numerosDePagina", () => {
  it("con pocas páginas las muestra todas", () => {
    expect(numerosDePagina(2, 5)).toEqual([1, 2, 3, 4, 5]);
  });

  it("con muchas resume con puntos suspensivos alrededor de la actual", () => {
    expect(numerosDePagina(1, 20)).toEqual([1, 2, "…", 20]);
    expect(numerosDePagina(10, 20)).toEqual([1, "…", 9, 10, 11, "…", 20]);
    expect(numerosDePagina(20, 20)).toEqual([1, "…", 19, 20]);
  });

  it("no pone puntos suspensivos para ocultar una sola página", () => {
    expect(numerosDePagina(4, 20)).toEqual([1, 2, 3, 4, 5, "…", 20]);
  });
});

describe("Paginacion", () => {
  it("dice qué rango se ve y marca la página actual", () => {
    render(<Paginacion pagina={2} total={40} porPagina={15} alCambiar={() => {}} />);
    expect(screen.getByText("16–30 de 40")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Página 2" })).toHaveAttribute("aria-current", "page");
  });

  it("anterior, siguiente y los números cambian de página", async () => {
    const alCambiar = vi.fn();
    render(<Paginacion pagina={2} total={40} porPagina={15} alCambiar={alCambiar} />);
    const nav = screen.getByRole("navigation", { name: /paginación/i });
    await userEvent.click(within(nav).getByRole("button", { name: /anterior/i }));
    await userEvent.click(within(nav).getByRole("button", { name: /siguiente/i }));
    await userEvent.click(within(nav).getByRole("button", { name: "Página 3" }));
    expect(alCambiar.mock.calls).toEqual([[1], [3], [3]]);
  });

  it("en los extremos desactiva el botón que no lleva a ningún lado", () => {
    const { rerender } = render(<Paginacion pagina={1} total={40} porPagina={15} alCambiar={() => {}} />);
    expect(screen.getByRole("button", { name: /anterior/i })).toBeDisabled();
    rerender(<Paginacion pagina={3} total={40} porPagina={15} alCambiar={() => {}} />);
    expect(screen.getByRole("button", { name: /siguiente/i })).toBeDisabled();
  });

  it("si todo cabe en una página no se muestra", () => {
    const { container } = render(<Paginacion pagina={1} total={15} porPagina={15} alCambiar={() => {}} />);
    expect(container).toBeEmptyDOMElement();
  });
});
