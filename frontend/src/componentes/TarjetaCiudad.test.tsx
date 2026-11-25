import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { comparacion, opcion } from "../pruebas/datos";
import { TarjetaCiudad } from "./TarjetaCiudad";

const FORT = comparacion("Fort Sterling", { directa: opcion("directa", 86_400), orden: opcion("orden", 93_500) });
const BLACK_MARKET = comparacion("Black Market", { directa: opcion("directa", 144_000) });
const VIEJA = comparacion("Thetford", {
  directa: opcion("directa", 500_000, { confiable: false, antiguedad_segundos: 18 * 3_600 }),
  confiable: false,
});

function pintar(c = FORT, { esMejor = false, puedeRegistrar = true, cantidad = 1 } = {}) {
  const alRegistrar = vi.fn();
  render(<TarjetaCiudad comparacion={c} esMejor={esMejor} puedeRegistrar={puedeRegistrar} cantidad={cantidad} alRegistrar={alRegistrar} />);
  return alRegistrar;
}

describe("TarjetaCiudad", () => {
  it("muestra la ciudad y marca las islas del gremio", () => {
    pintar();
    expect(screen.getByRole("heading", { name: "Fort Sterling" })).toBeInTheDocument();
    expect(screen.getByText("Tu isla")).toBeInTheDocument();
  });

  it("no marca como isla una ciudad que no es del gremio", () => {
    pintar(comparacion("Martlock", { directa: opcion("directa", 1_000) }));
    expect(screen.queryByText("Tu isla")).not.toBeInTheDocument();
  });

  it("compara venta directa contra orden, con el neto exacto al pasar el cursor", () => {
    pintar();
    expect(screen.getByTitle("86,400")).toHaveTextContent("86.4 k");
    expect(screen.getByTitle("93,500")).toHaveTextContent("93.5 k");
    expect(screen.getByText(/la orden deja/i)).toHaveTextContent("+7.1 k");
  });

  it("marca como ganadora la opción que más rinde", () => {
    pintar();
    const ganadora = screen.getByRole("group", { name: /orden de venta/i });
    expect(ganadora).toHaveAttribute("data-ganadora", "true");
    expect(screen.getByRole("group", { name: /venta directa/i })).toHaveAttribute("data-ganadora", "false");
  });

  it("dice 'Mejor opción' solo si se le indica", () => {
    pintar(FORT, { esMejor: true });
    expect(screen.getByText("Mejor opción")).toBeInTheDocument();
  });

  it("el Black Market explica que no admite órdenes de venta", () => {
    pintar(BLACK_MARKET);
    expect(screen.getByText(/solo admite venta directa/i)).toBeInTheDocument();
    expect(screen.queryByRole("group", { name: /orden de venta/i })).not.toBeInTheDocument();
  });

  it("un dato viejo se atenúa y dice de hace cuánto es", () => {
    pintar(VIEJA);
    expect(screen.getByRole("article")).toHaveClass("ciudad--vieja");
    expect(screen.getByText("Dato viejo")).toBeInTheDocument();
    expect(screen.getByText("hace 18 h")).toBeInTheDocument();
  });

  it("con varias unidades muestra el total y lo que rinde cada una", () => {
    pintar(comparacion("Lymhurst", { directa: opcion("directa", 432_000, { neto_unitario: 144_000 }) }), { cantidad: 3 });
    expect(screen.getByTitle("432,000")).toBeInTheDocument();
    expect(screen.getByText(/144,000 por unidad/i)).toBeInTheDocument();
  });

  it("una ciudad sin órdenes de compra lo dice", () => {
    pintar(comparacion("Martlock", { orden: opcion("orden", 5_000) }));
    expect(screen.getByText(/sin órdenes de compra/i)).toBeInTheDocument();
  });

  it("el admin puede registrar la venta desde la opción que quiera", async () => {
    const alRegistrar = pintar();
    await userEvent.click(within(screen.getByRole("group", { name: /orden de venta/i })).getByRole("button", { name: /registrar/i }));
    expect(alRegistrar).toHaveBeenCalledWith("Fort Sterling", "orden", FORT.orden!.precio_unitario);
  });

  it("un general no ve los botones de registrar", () => {
    pintar(FORT, { puedeRegistrar: false });
    expect(screen.queryByRole("button", { name: /registrar/i })).not.toBeInTheDocument();
  });
});
