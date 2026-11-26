import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ARMADURA, ESPADA } from "../pruebas/datos";
import { instalarApi, montarPagina } from "../pruebas/utiles";
import { SelectorObjeto } from "./SelectorObjeto";

const buscador = () => screen.getByRole("combobox", { name: /buscar objeto/i });

describe("SelectorObjeto", () => {
  it("busca después de escribir y muestra los resultados", async () => {
    const llamadas = instalarApi({ "GET /api/catalogo": [ESPADA, ARMADURA] });
    const alElegir = vi.fn();
    montarPagina(<SelectorObjeto valor={null} alElegir={alElegir} />);

    await userEvent.type(buscador(), "maestro");
    const opcion = await screen.findByRole("option", { name: /espada ancha del maestro/i });
    expect(screen.getAllByRole("option")).toHaveLength(2);
    expect(llamadas.at(-1)?.params).toMatchObject({ q: "maestro" });

    await userEvent.click(opcion);
    expect(alElegir).toHaveBeenCalledWith(ESPADA);
  });

  it("no busca con menos de dos letras y lo explica", async () => {
    const llamadas = instalarApi({ "GET /api/catalogo": [] });
    montarPagina(<SelectorObjeto valor={null} alElegir={() => {}} />);
    await userEvent.type(buscador(), "e");
    expect(screen.getByText(/escribe al menos 2 letras/i)).toBeInTheDocument();
    expect(llamadas).toHaveLength(0);
  });

  it("si no hay resultados lo dice", async () => {
    instalarApi({ "GET /api/catalogo": [] });
    montarPagina(<SelectorObjeto valor={null} alElegir={() => {}} />);
    await userEvent.type(buscador(), "zzzz");
    expect(await screen.findByText(/sin resultados para/i)).toBeInTheDocument();
  });

  it("se maneja con el teclado: flecha abajo y Enter eligen", async () => {
    instalarApi({ "GET /api/catalogo": [ESPADA, ARMADURA] });
    const alElegir = vi.fn();
    montarPagina(<SelectorObjeto valor={null} alElegir={alElegir} />);
    await userEvent.type(buscador(), "maestro");
    await screen.findAllByRole("option");
    await userEvent.keyboard("{ArrowDown}{ArrowDown}{Enter}");
    expect(alElegir).toHaveBeenCalledWith(ARMADURA);
  });

  it("Escape cierra la lista sin elegir nada", async () => {
    instalarApi({ "GET /api/catalogo": [ESPADA] });
    const alElegir = vi.fn();
    montarPagina(<SelectorObjeto valor={null} alElegir={alElegir} />);
    await userEvent.type(buscador(), "maestro");
    await screen.findByRole("option");
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("option")).not.toBeInTheDocument();
    expect(alElegir).not.toHaveBeenCalled();
  });

  it("con un objeto elegido muestra su nombre y deja cambiarlo", async () => {
    const alElegir = vi.fn();
    montarPagina(<SelectorObjeto valor={ESPADA} alElegir={alElegir} />);
    expect(screen.getByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /cambiar/i }));
    expect(alElegir).toHaveBeenCalledWith(null);
  });

  it("cada resultado muestra la imagen del objeto", async () => {
    instalarApi({ "GET /api/catalogo": [ESPADA, ARMADURA] });
    montarPagina(<SelectorObjeto valor={null} alElegir={() => {}} />);
    await userEvent.type(buscador(), "maestro");
    const opciones = await screen.findAllByRole("option");
    expect(opciones[0]!.querySelector("img")?.getAttribute("src")).toContain("/item/T6_MAIN_SWORD.png");
  });

  it("el objeto elegido se ve con el encantamiento y la calidad indicados", () => {
    const { container } = montarPagina(<SelectorObjeto valor={ESPADA} encantamiento={2} calidad={4} alElegir={() => {}} />);
    expect(container.querySelector("img")?.getAttribute("src")).toContain("/item/T6_MAIN_SWORD@2.png?quality=4");
  });

  it("con buscarSiempre deja buscar otro objeto sin pasar por «Cambiar»", async () => {
    instalarApi({ "GET /api/catalogo": [ARMADURA] });
    const alElegir = vi.fn();
    montarPagina(<SelectorObjeto valor={ESPADA} buscarSiempre alElegir={alElegir} />);
    expect(screen.getByText("Espada ancha del maestro")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cambiar/i })).not.toBeInTheDocument();
    await userEvent.type(buscador(), "soldado");
    await userEvent.click(await screen.findByRole("option"));
    expect(alElegir).toHaveBeenCalledWith(ARMADURA);
    expect(buscador()).toHaveValue("");
  });
});
