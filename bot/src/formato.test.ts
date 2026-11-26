import { antiguedad, etiquetaCalidad, plataCompleta, plataCorta, signo } from "./formato.js";

describe("plataCorta", () => {
  it.each([
    [0, "0"], [950, "950"], [3_200, "3.2 k"], [120_553_500, "120.6 M"], [120_000_000, "120 M"],
    [1_250_000_000, "1.3 B"], [-1_500_000, "-1.5 M"],
  ])("%d -> %s", (valor, esperado) => expect(plataCorta(valor)).toBe(esperado));
});

it("plataCompleta usa comas de miles", () => expect(plataCompleta(120_553_500)).toBe("120,553,500"));
it("signo antepone + a los positivos", () => {
  expect([signo(1_500), signo(-1_500), signo(0)]).toEqual(["+1.5 k", "-1.5 k", "0"]);
});
it.each([[10, "hace un momento"], [300, "hace 5 min"], [18 * 3_600, "hace 18 h"], [3 * 86_400, "hace 3 d"]])(
  "antiguedad %d s -> %s", (segundos, esperado) => expect(antiguedad(segundos)).toBe(esperado),
);
it("etiquetaCalidad traduce el número", () => {
  expect([1, 2, 3, 4, 5].map((n) => etiquetaCalidad(n))).toEqual(["Normal", "Buena", "Notable", "Sobresaliente", "Obra maestra"]);
});
