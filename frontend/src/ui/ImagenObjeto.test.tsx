import { fireEvent, render, screen } from "@testing-library/react";
import { ImagenObjeto, urlImagenObjeto } from "./ImagenObjeto";

describe("urlImagenObjeto", () => {
  it("usa el servicio oficial de Albion, con calidad y tamaño", () => {
    expect(urlImagenObjeto("T6_MAIN_SWORD", 0, 1, 64)).toBe(
      "https://render.albiononline.com/v1/item/T6_MAIN_SWORD.png?quality=1&size=64",
    );
  });

  it("el encantamiento va con @ y solo si es mayor que 0", () => {
    expect(urlImagenObjeto("T6_MAIN_SWORD", 2, 4, 64)).toContain("/T6_MAIN_SWORD@2.png?quality=4");
  });

  it("no pide más de 217 px, el máximo del servicio", () => {
    expect(urlImagenObjeto("T4_BAG", 0, 1, 400)).toContain("size=217");
  });
});

describe("ImagenObjeto", () => {
  it("es decorativa (el nombre ya está escrito al lado) y pide el doble para pantallas nítidas", () => {
    const { container } = render(<ImagenObjeto baseId="T6_MAIN_SWORD" encantamiento={1} calidad={3} tamano={48} />);
    const img = container.querySelector("img")!;
    expect(img.getAttribute("alt")).toBe("");
    expect(img.getAttribute("width")).toBe("48");
    expect(img.getAttribute("loading")).toBe("lazy");
    expect(img.getAttribute("src")).toBe("https://render.albiononline.com/v1/item/T6_MAIN_SWORD@1.png?quality=3&size=96");
  });

  it("si la imagen no carga deja un hueco del mismo tamaño en vez del ícono roto", () => {
    const { container } = render(<ImagenObjeto baseId="T6_MAIN_SWORD" tamano={40} />);
    fireEvent.error(container.querySelector("img")!);
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector(".imagen-objeto--vacia")).not.toBeNull();
  });

  it("al cambiar de objeto vuelve a intentarlo", () => {
    const { container, rerender } = render(<ImagenObjeto baseId="T6_MAIN_SWORD" tamano={40} />);
    fireEvent.error(container.querySelector("img")!);
    rerender(<ImagenObjeto baseId="T5_MAIN_AXE" tamano={40} />);
    expect(container.querySelector("img")?.getAttribute("src")).toContain("T5_MAIN_AXE");
    expect(screen.queryByRole("img")).toBeNull(); // alt vacío: no se anuncia
  });
});
