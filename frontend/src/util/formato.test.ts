import {
  antiguedad,
  diaCorto,
  diaLocalHaceDias,
  etiquetaCalidad,
  fechaHora,
  finDelDia,
  inicioDelDia,
  plataCompleta,
  plataCorta,
  signo,
} from "./formato";

describe("plataCorta", () => {
  it.each([
    [0, "0"],
    [950, "950"],
    [1_000, "1 k"],
    [3_200, "3.2 k"],
    [999_999, "1000 k"],
    [1_000_000, "1 M"],
    [120_553_500, "120.6 M"],
    [120_000_000, "120 M"],
    [1_250_000_000, "1.3 B"],
    [-1_500_000, "-1.5 M"],
    [-950, "-950"],
  ])("%d se muestra como %s", (valor, esperado) => {
    expect(plataCorta(valor)).toBe(esperado);
  });
});

describe("plataCompleta", () => {
  it("usa comas de miles como en México", () => {
    expect(plataCompleta(120_553_500)).toBe("120,553,500");
    expect(plataCompleta(-5_000)).toBe("-5,000");
  });
});

describe("signo", () => {
  it("antepone + a los positivos", () => {
    expect(signo(1_500_000)).toBe("+1.5 M");
    expect(signo(-1_500_000)).toBe("-1.5 M");
    expect(signo(0)).toBe("0");
  });
});

describe("antiguedad", () => {
  it.each([
    [10, "hace un momento"],
    [300, "hace 5 min"],
    [3_600, "hace 1 h"],
    [18 * 3_600 + 120, "hace 18 h"],
    [3 * 86_400, "hace 3 d"],
  ])("%d s -> %s", (segundos, esperado) => {
    expect(antiguedad(segundos)).toBe(esperado);
  });
});

describe("etiquetaCalidad", () => {
  it("traduce el número de calidad", () => {
    expect([1, 2, 3, 4, 5].map(etiquetaCalidad)).toEqual([
      "Normal", "Buena", "Notable", "Sobresaliente", "Obra maestra",
    ]);
  });
});

describe("fechas para mostrar", () => {
  it("fechaHora muestra día, mes, año y hora en el formato de México", () => {
    const local = new Date(2026, 10, 25, 14, 5).toISOString();
    expect(fechaHora(local)).toBe("25/11/2026 14:05");
  });

  it("diaCorto muestra el día y el mes abreviado sin punto", () => {
    expect(diaCorto("2026-11-25")).toBe("25 nov");
    expect(diaCorto("2026-01-03")).toBe("3 ene");
  });
});

describe("diaLocalHaceDias", () => {
  afterEach(() => vi.useRealTimers());

  it("devuelve el día local de hace n días, cruzando de mes si hace falta", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 2, 2, 12)); // 2 de marzo de 2026
    expect(diaLocalHaceDias(0)).toBe("2026-03-02");
    expect(diaLocalHaceDias(5)).toBe("2026-02-25");
    expect(diaLocalHaceDias(30)).toBe("2026-01-31");
  });
});

describe("rango de un día en hora local", () => {
  it("empieza a las 00:00 y termina a las 23:59:59 del mismo día local", () => {
    const inicio = new Date(inicioDelDia("2026-11-25"));
    const fin = new Date(finDelDia("2026-11-25"));
    expect([inicio.getFullYear(), inicio.getMonth(), inicio.getDate(), inicio.getHours(), inicio.getMinutes()]).toEqual([2026, 10, 25, 0, 0]);
    expect([fin.getDate(), fin.getHours(), fin.getMinutes(), fin.getSeconds()]).toEqual([25, 23, 59, 59]);
  });
});
