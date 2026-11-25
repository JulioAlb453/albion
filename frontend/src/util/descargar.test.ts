import { guardarArchivo } from "./descargar";

describe("guardarArchivo", () => {
  it("dispara la descarga con el nombre que se le da y libera la dirección temporal", () => {
    vi.useFakeTimers();
    const crear = vi.fn(() => "blob:falso");
    const liberar = vi.fn();
    vi.stubGlobal("URL", Object.assign(URL, { createObjectURL: crear, revokeObjectURL: liberar }));
    const descargas: { nombre: string; destino: string }[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      descargas.push({ nombre: this.download, destino: this.href });
    });

    guardarArchivo(new Blob(["a,b"]), "ventas-2026-11-25.csv");

    expect(descargas).toEqual([{ nombre: "ventas-2026-11-25.csv", destino: "blob:falso" }]);
    expect(document.querySelector("a[download]")).toBeNull(); // no deja el enlace en la página
    vi.runAllTimers();
    expect(liberar).toHaveBeenCalledWith("blob:falso");
    vi.useRealTimers();
    vi.restoreAllMocks();
  });
});
