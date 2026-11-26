import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ESPADA, OBJETO_ESPADA, venta } from "../pruebas/datos";
import { instalarApi, montarPagina, ultimaDescarga, USUARIO_GENERAL } from "../pruebas/utiles";
import { guardarArchivo } from "../util/descargar";
import { finDelDia, inicioDelDia } from "../util/formato";
import { Ventas } from "./Ventas";

vi.mock("../util/descargar", () => ({ guardarArchivo: vi.fn() }));

const ARMADURA = { ...OBJETO_ESPADA, base_id: "T6_ARMOR_PLATE_SET1", nombre: "Armadura de soldado del maestro", etiqueta: "T6.0", encantamiento: 0 };
const VENTAS = [
  venta({ id: 1, fecha: "2026-11-24T10:00:00Z" }),
  venta({ id: 2, objeto: ARMADURA, ciudad: "Caerleon", tipo: "orden", cantidad: 1, precio_unitario: 100_000, bruto: 100_000, impuesto: 4_000, tarifa_publicacion: 2_500, neto: 93_500, fecha: "2026-11-25T18:00:00Z" }),
];
const RUTAS = {
  "GET /api/ventas": VENTAS,
  "GET /api/ingresos": [],
  "DELETE /api/ventas/1": new Response(null, { status: 204 }),
};
const ultima = (llamadas: ReturnType<typeof instalarApi>, ruta = "/api/ventas") => llamadas.filter((l) => l.ruta === ruta).at(-1)!;

describe("lista", () => {
  it("muestra cada venta con su objeto, ciudad, tipo y neto, y los totales", async () => {
    instalarApi(RUTAS);
    montarPagina(<Ventas />);
    const tabla = await screen.findByRole("table");
    const filas = within(tabla).getAllByRole("row");
    expect(filas).toHaveLength(1 + 2 + 1); // encabezado, dos ventas y totales
    // la más reciente arriba (la API las manda de la más vieja a la más nueva)
    expect(within(filas[1]!).getByText("Armadura de soldado del maestro")).toBeInTheDocument();
    expect(within(filas[1]!).getByText("Caerleon")).toBeInTheDocument();
    expect(within(filas[2]!).getByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(within(filas[3]!).getByText(/2 ventas/i)).toBeInTheDocument();
    // neto total 192,000 + 93,500; cargos 8,000 + 6,500
    expect(within(filas[3]!).getByTitle("285,500")).toBeInTheDocument();
    expect(within(filas[3]!).getByTitle("14,500")).toBeInTheDocument();
  });

  it("cada venta dice su encantamiento y su calidad, con la imagen del objeto", async () => {
    instalarApi(RUTAS);
    const { container } = montarPagina(<Ventas />);
    const tabla = await screen.findByRole("table");
    const [, armadura, espada] = within(tabla).getAllByRole("row");
    expect(within(espada!).getByText(/encantamiento \.2/i)).toBeInTheDocument();
    expect(within(espada!).getByText(/sobresaliente/i)).toBeInTheDocument();
    expect(within(armadura!).getByText(/sin encantar/i)).toBeInTheDocument();
    expect(container.querySelector('img[src*="T6_MAIN_SWORD@2.png?quality=4"]')).not.toBeNull();
  });

  it("sin ventas invita a registrar la primera", async () => {
    instalarApi({ "GET /api/ventas": [] });
    montarPagina(<Ventas />);
    expect(await screen.findByText(/todavía no hay ventas/i)).toBeInTheDocument();
  });

  it("si la lista no carga lo dice y deja reintentar", async () => {
    instalarApi({});
    montarPagina(<Ventas />);
    const aviso = (await screen.findByText(/no se pudo cargar las ventas/i)).closest("[role=alert]") as HTMLElement;
    expect(within(aviso).getByRole("button", { name: /reintentar/i })).toBeInTheDocument();
  });
});

describe("paginación", () => {
  // 40 ventas de 1 de plata neta cada una
  const MUCHAS = Array.from({ length: 40 }, (_, n) =>
    venta({ id: n + 1, neto: 1, fecha: `2026-11-${String(Math.floor(n / 2) + 1).padStart(2, "0")}T${n % 2 ? "18" : "10"}:00:00Z` }),
  );
  const filasDeVentas = () => within(screen.getByRole("table")).getAllByRole("row").slice(1, -1);

  it("muestra 15 por página y los totales cubren todas", async () => {
    instalarApi({ ...RUTAS, "GET /api/ventas": MUCHAS });
    montarPagina(<Ventas />);
    await screen.findByRole("table");
    expect(filasDeVentas()).toHaveLength(15);
    expect(screen.getByText(/40 ventas/i)).toBeInTheDocument();
    expect(screen.getByTitle("40")).toBeInTheDocument();
    expect(screen.getByText("1–15 de 40")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Página 3" }));
    expect(filasDeVentas()).toHaveLength(10);
    expect(screen.getByText("31–40 de 40")).toBeInTheDocument();
  });

  it("cambiar un filtro vuelve a la primera página", async () => {
    instalarApi({ ...RUTAS, "GET /api/ventas": MUCHAS });
    montarPagina(<Ventas />);
    await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", { name: "Página siguiente" }));
    expect(screen.getByRole("button", { name: "Página 2" })).toHaveAttribute("aria-current", "page");
    await userEvent.selectOptions(screen.getByLabelText(/ciudad/i), "Caerleon");
    expect(await screen.findByText("1–15 de 40")).toBeInTheDocument();
  });

  it("con 15 o menos no aparece", async () => {
    instalarApi(RUTAS);
    montarPagina(<Ventas />);
    await screen.findByRole("table");
    expect(screen.queryByRole("navigation", { name: /paginación/i })).not.toBeInTheDocument();
  });
});

describe("filtros", () => {
  it("pide solo lo que se filtra: ciudad, tipo y fechas en hora local", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Ventas />);
    await screen.findByRole("table");
    expect(ultima(llamadas).params).toEqual({});

    await userEvent.selectOptions(screen.getByLabelText(/ciudad/i), "Caerleon");
    await userEvent.selectOptions(screen.getByLabelText(/tipo/i), "orden");
    fireEvent.change(screen.getByLabelText(/desde/i), { target: { value: "2026-11-20" } });
    fireEvent.change(screen.getByLabelText(/hasta/i), { target: { value: "2026-11-25" } });

    await waitFor(() =>
      expect(ultima(llamadas).params).toEqual({
        ciudad: "Caerleon", tipo: "orden", desde: inicioDelDia("2026-11-20"), hasta: finDelDia("2026-11-25"),
      }),
    );
  });
});

describe("exportar", () => {
  it("baja el archivo en CSV o Excel con los mismos filtros", async () => {
    const respuesta = () => new Response("a,b", { headers: { "content-disposition": 'attachment; filename="ventas-2026-11-25.csv"' } });
    const llamadas = instalarApi({ ...RUTAS, "GET /api/ventas/exportar": respuesta });
    montarPagina(<Ventas />);
    await screen.findByRole("table");
    await userEvent.selectOptions(screen.getByLabelText(/ciudad/i), "Caerleon");

    await userEvent.click(screen.getByRole("button", { name: /exportar csv/i }));
    await waitFor(() => expect(guardarArchivo).toHaveBeenCalled());
    expect(await ultimaDescarga()).toEqual({ nombre: "ventas-2026-11-25.csv", contenido: "a,b" });
    expect(ultima(llamadas, "/api/ventas/exportar").params).toEqual({ ciudad: "Caerleon", formato: "csv" });

    await userEvent.click(screen.getByRole("button", { name: /exportar excel/i }));
    await waitFor(() => expect(ultima(llamadas, "/api/ventas/exportar").params.formato).toBe("xlsx"));
  });
});

describe("permisos y acciones", () => {
  it("el admin elimina una venta confirmando en dos pasos", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Ventas />);
    await screen.findByRole("table");
    // la venta 1 (Espada) es la segunda fila, porque la más reciente va arriba
    await userEvent.click(screen.getByRole("button", { name: /eliminar venta de espada/i }));
    expect(llamadas.some((l) => l.metodo === "DELETE")).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: /confirmar eliminación/i }));
    await waitFor(() => expect(llamadas.some((l) => l.metodo === "DELETE" && l.ruta === "/api/ventas/1")).toBe(true));
    expect(await screen.findByText(/venta eliminada/i)).toBeInTheDocument();
  });

  it("el admin corrige el encantamiento que olvidó poner", async () => {
    const corregida = venta({ id: 1, objeto: { ...OBJETO_ESPADA, encantamiento: 3, etiqueta: "T6.3" }, fecha: "2026-11-24T10:00:00Z" });
    const llamadas = instalarApi({ ...RUTAS, "GET /api/catalogo/T6_MAIN_SWORD": ESPADA, "PATCH /api/ventas/1": corregida });
    montarPagina(<Ventas />);
    await screen.findByRole("table");
    await userEvent.click(screen.getByRole("button", { name: /corregir venta de espada/i }));
    const dialogo = screen.getByRole("dialog", { name: /corregir venta/i });
    const encantamiento = await within(dialogo).findByRole("combobox", { name: /encantamiento/i });
    expect(encantamiento).toHaveValue("2"); // empieza con lo que tenía
    await userEvent.selectOptions(encantamiento, "3");
    await userEvent.click(within(dialogo).getByRole("button", { name: /guardar/i }));
    await waitFor(() => expect(llamadas.find((l) => l.metodo === "PATCH")).toMatchObject({
      ruta: "/api/ventas/1", cuerpo: { encantamiento: 3, calidad: 4 },
    }));
    expect(await screen.findByText(/venta corregida/i)).toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: /corregir venta/i })).not.toBeInTheDocument();
  });

  it("el admin puede importar (registrar una venta está siempre en la barra superior)", async () => {
    instalarApi(RUTAS);
    montarPagina(<Ventas />);
    await screen.findByRole("table");
    expect(screen.queryByRole("button", { name: /registrar venta/i })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /^importar$/i }));
    expect(screen.getByRole("dialog", { name: /importar ventas/i })).toBeInTheDocument();
  });

  it("un general solo consulta y exporta: no ve registrar, importar ni eliminar", async () => {
    instalarApi(RUTAS);
    montarPagina(<Ventas />, { usuario: USUARIO_GENERAL });
    await screen.findByRole("table");
    expect(screen.queryByRole("button", { name: /registrar venta/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^importar$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /eliminar venta/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /corregir venta/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /exportar csv/i })).toBeInTheDocument();
  });
});
