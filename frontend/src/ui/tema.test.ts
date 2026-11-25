import { aplicarTema, temaInicial } from "./tema";

function sistemaPrefiere(esquema: "light" | "dark") {
  vi.stubGlobal("matchMedia", (consulta: string) => ({
    matches: consulta.includes("light") && esquema === "light",
    media: consulta,
  }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  delete document.documentElement.dataset.tema;
});

describe("temaInicial", () => {
  it("arranca en oscuro si el sistema no dice otra cosa", () => {
    expect(temaInicial()).toBe("oscuro");
  });

  it("respeta la preferencia clara del sistema", () => {
    sistemaPrefiere("light");
    expect(temaInicial()).toBe("claro");
  });

  it("lo que la persona eligió gana sobre el sistema", () => {
    sistemaPrefiere("light");
    localStorage.setItem("gremio.tema", "oscuro");
    expect(temaInicial()).toBe("oscuro");
  });

  it("ignora un valor guardado que no es un tema", () => {
    localStorage.setItem("gremio.tema", "morado");
    expect(temaInicial()).toBe("oscuro");
  });
});

describe("aplicarTema", () => {
  it("lo pone en la página y lo recuerda", () => {
    aplicarTema("claro");
    expect(document.documentElement.dataset.tema).toBe("claro");
    expect(localStorage.getItem("gremio.tema")).toBe("claro");
  });
});
