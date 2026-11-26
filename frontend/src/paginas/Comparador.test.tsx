import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ARTEFACTO, comparacion, ESPADA, opcion } from "../pruebas/datos";
import { instalarApi, json, montarPagina, USUARIO_GENERAL } from "../pruebas/utiles";
import { Comparador } from "./Comparador";

const COMPARACIONES = [
  comparacion("Black Market", { directa: opcion("directa", 144_000) }),
  comparacion("Caerleon", { orden: opcion("orden", 112_200) }),
  comparacion("Fort Sterling", { directa: opcion("directa", 86_400), orden: opcion("orden", 93_500) }),
  comparacion("Thetford", { directa: opcion("directa", 900_000, { confiable: false }), confiable: false }),
];
const RUTA = "/comparador?base_id=T6_MAIN_SWORD&enc=2&cal=4";
const RUTAS = { "GET /api/catalogo/T6_MAIN_SWORD": ESPADA, "GET /api/mercado/comparar": COMPARACIONES };
const ciudades = () => screen.getAllByRole("article").map((a) => within(a).getByRole("heading").textContent);

describe("Comparador", () => {
  it("sin objeto invita a elegir uno y no consulta precios", () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Comparador />, { ruta: "/comparador" });
    expect(screen.getByText(/elige un objeto para comparar/i)).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: /buscar objeto/i })).toBeInTheDocument();
    expect(llamadas.filter((l) => l.ruta.includes("comparar"))).toHaveLength(0);
  });

  it("desde un enlace carga el objeto y compara sus precios con los parámetros del enlace", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Comparador />, { ruta: RUTA });
    expect(await screen.findByText("Espada ancha del maestro")).toBeInTheDocument();
    await screen.findAllByRole("article");
    expect(llamadas.find((l) => l.ruta === "/api/mercado/comparar")?.params).toEqual({
      base_id: "T6_MAIN_SWORD", encantamiento: "2", calidad: "4", cantidad: "1",
    });
    expect(ciudades()).toEqual(["Black Market", "Caerleon", "Fort Sterling", "Thetford"]);
  });

  it("solo la primera ciudad con dato reciente es la mejor opción", async () => {
    instalarApi(RUTAS);
    montarPagina(<Comparador />, { ruta: RUTA });
    await screen.findAllByRole("article");
    const marcadas = screen.getAllByText("Mejor opción");
    expect(marcadas).toHaveLength(1);
    expect(screen.getAllByRole("article")[0]).toContainElement(marcadas[0]!);
  });

  it("si la mejor ciudad de la lista tuviera dato viejo, no se corona", async () => {
    instalarApi({ ...RUTAS, "GET /api/mercado/comparar": [COMPARACIONES[3]] });
    montarPagina(<Comparador />, { ruta: RUTA });
    await screen.findAllByRole("article");
    expect(screen.queryByText("Mejor opción")).not.toBeInTheDocument();
    expect(screen.getByText("Dato viejo")).toBeInTheDocument();
  });

  it("un artefacto no tiene encantamiento ni calidad", async () => {
    instalarApi({ "GET /api/catalogo/T4_ARTEFACT_2H_BOW_KEEPER": ARTEFACTO, "GET /api/mercado/comparar": COMPARACIONES });
    montarPagina(<Comparador />, { ruta: "/comparador?base_id=T4_ARTEFACT_2H_BOW_KEEPER" });
    await screen.findByText("Hueso tallado del iniciado");
    expect(screen.queryByLabelText(/encantamiento/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/calidad/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/cantidad/i)).toBeInTheDocument();
  });

  it("cambiar el encantamiento o la cantidad vuelve a consultar", async () => {
    const llamadas = instalarApi(RUTAS);
    montarPagina(<Comparador />, { ruta: RUTA });
    await screen.findAllByRole("article");
    await userEvent.selectOptions(screen.getByLabelText(/encantamiento/i), "3");
    await userEvent.clear(screen.getByLabelText(/cantidad/i));
    await userEvent.type(screen.getByLabelText(/cantidad/i), "5");
    await screen.findAllByRole("article");
    const ultima = llamadas.filter((l) => l.ruta === "/api/mercado/comparar").at(-1);
    expect(ultima?.params).toMatchObject({ encantamiento: "3", cantidad: "5" });
  });

  it("si la API de Albion falla lo dice y deja reintentar", async () => {
    instalarApi({ ...RUTAS, "GET /api/mercado/comparar": json({ detail: "La API de Albion no respondió" }, 502) });
    montarPagina(<Comparador />, { ruta: RUTA });
    expect(await screen.findByText(/la api de albion no respondió/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeInTheDocument();
  });

  it("si ninguna ciudad tiene datos lo explica", async () => {
    instalarApi({ ...RUTAS, "GET /api/mercado/comparar": [] });
    montarPagina(<Comparador />, { ruta: RUTA });
    expect(await screen.findByText(/nadie ha reportado precios/i)).toBeInTheDocument();
  });

  it("el admin registra una venta con los datos de la opción elegida ya cargados", async () => {
    instalarApi(RUTAS);
    const abrirVenta = vi.fn();
    montarPagina(<Comparador />, { ruta: RUTA, registro: { abrirVenta } });
    const tarjeta = (await screen.findAllByRole("article"))[0]!;
    await userEvent.click(within(tarjeta).getByRole("button", { name: /registrar/i }));
    expect(abrirVenta).toHaveBeenCalledWith({
      objeto: ESPADA, encantamiento: 2, calidad: 4, cantidad: 1,
      ciudad: "Black Market", tipo: "directa", precio_unitario: COMPARACIONES[0]!.directa!.precio_unitario,
    });
  });

  it("un general consulta pero no ve los botones de registrar", async () => {
    instalarApi(RUTAS);
    montarPagina(<Comparador />, { ruta: RUTA, usuario: USUARIO_GENERAL });
    await screen.findAllByRole("article");
    expect(screen.queryByRole("button", { name: /registrar/i })).not.toBeInTheDocument();
  });

  it("la imagen del objeto cambia con el encantamiento elegido", async () => {
    instalarApi(RUTAS);
    const { container } = montarPagina(<Comparador />, { ruta: RUTA });
    await screen.findByText("Espada ancha del maestro");
    expect(container.querySelector("img")?.getAttribute("src")).toContain("T6_MAIN_SWORD@2.png?quality=4");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: /encantamiento/i }), "3");
    expect(container.querySelector("img")?.getAttribute("src")).toContain("T6_MAIN_SWORD@3.png?quality=4");
  });
});
