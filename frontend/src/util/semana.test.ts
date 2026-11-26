import { etiquetaSemana, hoyServidor, lunesDe, moverSemanas } from "./semana";

describe("semanas de lunes a domingo (hora del servidor, UTC)", () => {
  it.each(["2026-11-23", "2026-11-25", "2026-11-29"])("%s es de la semana del lunes 23", (dia) => {
    expect(lunesDe(dia)).toBe("2026-11-23");
  });

  it("el lunes siguiente empieza otra semana", () => expect(lunesDe("2026-11-30")).toBe("2026-11-30"));

  it("se mueve de semana en semana, cruzando meses", () => {
    expect(moverSemanas("2026-11-23", 1)).toBe("2026-11-30");
    expect(moverSemanas("2026-11-23", -1)).toBe("2026-11-16");
    expect(moverSemanas("2026-12-28", 1)).toBe("2027-01-04");
  });

  it("dice de qué día a qué día va", () => {
    expect(etiquetaSemana("2026-11-23")).toBe("23 nov – 29 nov");
  });

  it("el día de hoy se toma en UTC, como el juego", () => {
    expect(hoyServidor(new Date("2026-11-30T02:00:00-06:00"))).toBe("2026-11-30"); // domingo 20:00 en México
  });
});
