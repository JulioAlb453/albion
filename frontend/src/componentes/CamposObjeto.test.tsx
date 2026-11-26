import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ObjetoCatalogo } from "../api/tipos";
import { ARTEFACTO, ESPADA } from "../pruebas/datos";
import { CamposObjeto, admiteOpciones, ajustar } from "./CamposObjeto";

const GUISO: ObjetoCatalogo = {
  base_id: "T8_MEAL_STEW", nombre: "Guiso de ternera", categoria: "consumible",
  tiene_calidad: false, encantamiento_min: 0, encantamiento_max: 3,
};
const MINERAL_RARO: ObjetoCatalogo = {
  base_id: "T4_ORE_LEVEL2", nombre: "Mineral de hierro raro", categoria: "recurso",
  tiene_calidad: false, encantamiento_min: 2, encantamiento_max: 2,
};

describe("ajustar", () => {
  it("lleva encantamiento y calidad a lo que admite el objeto", () => {
    expect(ajustar(ESPADA, 3, 4)).toEqual({ encantamiento: 3, calidad: 4 });
    expect(ajustar(GUISO, 4, 5)).toEqual({ encantamiento: 3, calidad: 1 });
    expect(ajustar(MINERAL_RARO, 0, 3)).toEqual({ encantamiento: 2, calidad: 1 });
    expect(ajustar(ARTEFACTO, 2, 2)).toEqual({ encantamiento: 0, calidad: 1 });
  });

  it("admiteOpciones dice si hay algo que elegir", () => {
    expect([ESPADA, GUISO, MINERAL_RARO, ARTEFACTO].map(admiteOpciones)).toEqual([true, true, false, false]);
  });
});

describe("CamposObjeto", () => {
  const montar = (objeto: ObjetoCatalogo, encantamiento = 0, calidad = 1) => {
    const alEncantamiento = vi.fn();
    const alCalidad = vi.fn();
    render(
      <CamposObjeto objeto={objeto} encantamiento={encantamiento} calidad={calidad}
        alCambiarEncantamiento={alEncantamiento} alCambiarCalidad={alCalidad} />,
    );
    return { alEncantamiento, alCalidad };
  };

  it("equipo: encantamiento 0 a 4 y calidad", () => {
    montar(ESPADA);
    expect(screen.getAllByRole("option", { name: /^\./ }).map((o) => o.textContent)).toHaveLength(5);
    expect(screen.getByRole("combobox", { name: /calidad/i })).toBeInTheDocument();
  });

  it("comida: solo encantamiento, hasta su máximo", async () => {
    const { alEncantamiento } = montar(GUISO);
    expect(screen.queryByRole("combobox", { name: /calidad/i })).not.toBeInTheDocument();
    const select = screen.getByRole("combobox", { name: /encantamiento/i });
    expect([...select.querySelectorAll("option")].map((o) => o.value)).toEqual(["0", "1", "2", "3"]);
    await userEvent.selectOptions(select, "2");
    expect(alEncantamiento).toHaveBeenCalledWith(2);
  });

  it("recurso con encantamiento fijo o artefacto: nada que elegir", () => {
    montar(MINERAL_RARO);
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });
});
