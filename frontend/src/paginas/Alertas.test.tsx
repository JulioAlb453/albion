import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Alerta, Seguimiento } from "../api/tipos";
import { ESPADA, OBJETO_ESPADA } from "../pruebas/datos";
import { instalarApi, montarPagina, USUARIO_GENERAL } from "../pruebas/utiles";
import { Alertas } from "./Alertas";

const SEGUIMIENTOS: Seguimiento[] = [
  { id: 1, objeto: OBJETO_ESPADA, ciudad_referencia: "Fort Sterling", porcentaje_minimo: 15, neto_minimo: null },
  { id: 2, objeto: { ...OBJETO_ESPADA, base_id: "T6_OFF_SHIELD", nombre: "Escudo del maestro", etiqueta: "T6.3", encantamiento: 3, calidad: 5 }, ciudad_referencia: "Lymhurst", porcentaje_minimo: null, neto_minimo: 300_000 },
];
const ALERTAS: Alerta[] = [
  { id: 1, seguimiento_id: 1, objeto: OBJETO_ESPADA, ciudad: "Black Market", tipo: "directa", neto_unitario: 144_000, neto_referencia: 93_500, motivo: "Black Market paga 54.0% más neto que Fort Sterling", fecha: "2026-11-25T12:00:00Z" },
];
const RUTAS = {
  "GET /api/seguimientos": SEGUIMIENTOS,
  "GET /api/alertas": ALERTAS,
  "DELETE /api/seguimientos/1": new Response(null, { status: 204 }),
  "GET /api/catalogo/T6_MAIN_SWORD": ESPADA,
};
const bloque = (titulo: string | RegExp) => within(screen.getByRole("heading", { name: titulo }).closest("section")!);

describe("objetos vigilados", () => {
  it("lista cada objeto con su criterio y la ciudad de referencia", async () => {
    instalarApi(RUTAS);
    montarPagina(<Alertas />);
    const vigilados = bloque("Objetos vigilados");
    expect(await vigilados.findByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(vigilados.getByText(/\+15 % sobre Fort Sterling/)).toBeInTheDocument();
    expect(vigilados.getByText("Escudo del maestro")).toBeInTheDocument();
    expect(vigilados.getByText(/neto por unidad ≥ 300 k/)).toBeInTheDocument();
  });

  it("sin objetos vigilados lo explica", async () => {
    instalarApi({ ...RUTAS, "GET /api/seguimientos": [] });
    montarPagina(<Alertas />);
    expect(await bloque("Objetos vigilados").findByText(/todavía no vigilas ningún objeto/i)).toBeInTheDocument();
  });

  it("el admin deja de vigilar uno confirmando en dos pasos", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Alertas />);
    await bloque("Objetos vigilados").findByText("Espada ancha del maestro");
    await userEvent.click(screen.getAllByRole("button", { name: /dejar de vigilar/i })[0]!);
    expect(llamadas.some((l) => l.metodo === "DELETE")).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: /confirmar/i }));
    await waitFor(() => expect(llamadas.some((l) => l.metodo === "DELETE" && l.ruta === "/api/seguimientos/1")).toBe(true));
  });

  it("el admin abre el formulario para vigilar un objeto nuevo", async () => {
    instalarApi(RUTAS);
    montarPagina(<Alertas />);
    await userEvent.click(await screen.findByRole("button", { name: /vigilar un objeto/i }));
    expect(screen.getByRole("dialog", { name: /vigilar un objeto/i })).toBeInTheDocument();
  });

  it("un general consulta pero no puede vigilar ni dejar de vigilar", async () => {
    instalarApi(RUTAS);
    montarPagina(<Alertas />, { usuario: USUARIO_GENERAL });
    await bloque("Objetos vigilados").findByText("Espada ancha del maestro");
    expect(screen.queryByRole("button", { name: /vigilar un objeto/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /dejar de vigilar/i })).not.toBeInTheDocument();
  });

  it("desde un enlace del comparador abre el formulario con el objeto ya elegido", async () => {
    instalarApi(RUTAS);
    montarPagina(<Alertas />, { ruta: "/alertas?base_id=T6_MAIN_SWORD&enc=2&cal=4" });
    const dialogo = await screen.findByRole("dialog", { name: /vigilar un objeto/i });
    expect(await within(dialogo).findByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(within(dialogo).getByLabelText(/encantamiento/i)).toHaveValue("2");
    expect(within(dialogo).getByLabelText(/calidad/i)).toHaveValue("4");
  });
});

describe("alertas recientes", () => {
  it("muestra cada alerta con su objeto, ciudad, motivo y neto", async () => {
    instalarApi(RUTAS);
    montarPagina(<Alertas />);
    const alertas = bloque("Alertas recientes");
    expect(await alertas.findByText(/black market paga 54\.0% más neto/i)).toBeInTheDocument();
    expect(alertas.getByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(alertas.getByTitle("144,000")).toHaveTextContent("144 k");
  });

  it("sin alertas explica cada cuánto se revisa", async () => {
    instalarApi({ ...RUTAS, "GET /api/alertas": [] });
    montarPagina(<Alertas />);
    expect(await bloque("Alertas recientes").findByText(/sin alertas todavía/i)).toBeInTheDocument();
  });

  it("si no cargan lo dice", async () => {
    instalarApi({ "GET /api/seguimientos": SEGUIMIENTOS });
    montarPagina(<Alertas />);
    expect(await screen.findByText(/no se pudo cargar las alertas/i)).toBeInTheDocument();
  });
});
