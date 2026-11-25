import { calcularDesglose } from "./desglose";

describe("calcularDesglose", () => {
  it("la venta directa paga solo el 4 % de impuesto", () => {
    expect(calcularDesglose(100_000, 3, "directa")).toEqual({
      bruto: 300_000, impuesto: 12_000, tarifa: 0, neto: 288_000,
    });
  });

  it("la orden de venta paga además el 2.5 % de tarifa de publicación", () => {
    expect(calcularDesglose(100_000, 3, "orden")).toEqual({
      bruto: 300_000, impuesto: 12_000, tarifa: 7_500, neto: 280_500,
    });
  });

  it("los reajustes de una orden suman tarifa", () => {
    expect(calcularDesglose(100_000, 1, "orden", 1_000).tarifa).toBe(3_500);
  });

  it("una venta directa ignora los reajustes", () => {
    expect(calcularDesglose(100_000, 1, "directa", 1_000).tarifa).toBe(0);
  });

  it.each([
    [37, 1, 1],  // 4 % = 1.48 -> 1 ; 2.5 % = 0.925 -> 1
    [20, 1, 1],  // 4 % = 0.8 -> 1 ; 2.5 % = 0.5 exacto -> sube a 1 (mitad hacia arriba, como el servidor)
    [13, 1, 0],  // 4 % = 0.52 -> 1 ; 2.5 % = 0.325 -> 0
  ])("redondea como el servidor: precio %i da impuesto %i y tarifa %i", (precio, impuesto, tarifa) => {
    const d = calcularDesglose(precio, 1, "orden");
    expect([d.impuesto, d.tarifa]).toEqual([impuesto, tarifa]);
  });

  it("el neto siempre es bruto menos cargos", () => {
    const d = calcularDesglose(98_765, 7, "orden", 321);
    expect(d.neto).toBe(d.bruto - d.impuesto - d.tarifa);
  });
});
