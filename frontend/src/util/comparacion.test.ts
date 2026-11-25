import { comparacion, opcion } from "../pruebas/datos";
import { mejorCiudad, opcionGanadora, ventajaSobre } from "./comparacion";

const BLACK_MARKET = comparacion("Black Market", { directa: opcion("directa", 144_000) });
const CAERLEON = comparacion("Caerleon", { orden: opcion("orden", 112_200) });
const FORT = comparacion("Fort Sterling", { directa: opcion("directa", 86_400), orden: opcion("orden", 93_500) });
const VIEJA = comparacion("Thetford", { directa: opcion("directa", 900_000, { confiable: false }), confiable: false });

describe("opcionGanadora", () => {
  it("devuelve la opción que la API marcó como mejor", () => {
    expect(opcionGanadora(FORT)?.tipo).toBe("orden");
    expect(opcionGanadora(BLACK_MARKET)?.tipo).toBe("directa");
  });

  it("sin ninguna opción no hay ganadora", () => {
    expect(opcionGanadora(comparacion("Martlock", {}))).toBeNull();
  });
});

describe("mejorCiudad", () => {
  it("es la primera con dato reciente, aunque una vieja pague más", () => {
    expect(mejorCiudad([VIEJA, BLACK_MARKET, CAERLEON])?.ciudad).toBe("Black Market");
    expect(mejorCiudad([BLACK_MARKET, CAERLEON, VIEJA])?.ciudad).toBe("Black Market");
  });

  it("si todo es viejo, la primera de la lista", () => {
    expect(mejorCiudad([VIEJA])?.ciudad).toBe("Thetford");
  });

  it("sin ciudades no hay mejor", () => {
    expect(mejorCiudad([])).toBeNull();
  });
});

describe("ventajaSobre", () => {
  it("cuánto más neto paga la mejor ciudad que la de referencia, en porcentaje", () => {
    // 144000 contra 93500 (lo mejor de Fort Sterling): 54 % más
    expect(ventajaSobre([BLACK_MARKET, FORT], "Fort Sterling")).toBeCloseTo(54.01, 1);
  });

  it("si la mejor ciudad ya es la de referencia, no hay ventaja que mostrar", () => {
    expect(ventajaSobre([FORT, CAERLEON], "Fort Sterling")).toBeNull();
  });

  it("sin datos de la ciudad de referencia, no se puede calcular", () => {
    expect(ventajaSobre([BLACK_MARKET, CAERLEON], "Fort Sterling")).toBeNull();
  });
});
