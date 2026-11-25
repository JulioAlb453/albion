import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ContextoRegistro } from "../componentes/ContextoRegistro";
import { ContextoSesion } from "../sesion/ContextoSesion";
import { USUARIO_ADMIN, USUARIO_GENERAL } from "../pruebas/utiles";
import type { Usuario } from "../api/tipos";
import { Estructura } from "./Estructura";

function montar(usuario: Usuario, ruta = "/") {
  const cerrarSesion = vi.fn();
  render(
    <ContextoSesion value={{ usuario, cerrarSesion }}>
      <MemoryRouter initialEntries={[ruta]}>
        <Routes>
          <Route element={<Estructura />}>
            <Route index element={<p>contenido del panel</p>} />
            <Route path="ventas" element={<p>contenido de ventas</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </ContextoSesion>,
  );
  return { cerrarSesion };
}

afterEach(() => delete document.documentElement.dataset.tema);

describe("navegación", () => {
  it("enlaza las seis secciones y marca la actual", () => {
    montar(USUARIO_ADMIN, "/ventas");
    const nav = screen.getByRole("navigation", { name: /principal/i });
    for (const nombre of ["Panel", "Comparador", "Ventas", "Gastos", "Reportes", "Alertas"]) {
      expect(nav).toHaveTextContent(nombre);
    }
    expect(screen.getByRole("link", { name: "Ventas" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Panel" })).not.toHaveAttribute("aria-current");
  });

  it("muestra el contenido de la ruta y el título de la sección", () => {
    montar(USUARIO_ADMIN, "/ventas");
    expect(screen.getByText("contenido de ventas")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Ventas");
  });
});

describe("permisos", () => {
  it("el admin ve el botón de registrar una venta", () => {
    montar(USUARIO_ADMIN);
    expect(screen.getByRole("button", { name: /registrar venta/i })).toBeInTheDocument();
  });

  it("al pulsarlo abre el formulario de registrar venta", async () => {
    const abrirVenta = vi.fn();
    render(
      <ContextoSesion value={{ usuario: USUARIO_ADMIN, cerrarSesion: vi.fn() }}>
        <ContextoRegistro value={{ abrirVenta }}>
          <MemoryRouter>
            <Routes>
              <Route element={<Estructura />}>
                <Route index element={<p>panel</p>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </ContextoRegistro>
      </ContextoSesion>,
    );
    await userEvent.click(screen.getByRole("button", { name: /registrar venta/i }));
    expect(abrirVenta).toHaveBeenCalledOnce();
    expect(abrirVenta).toHaveBeenCalledWith();
  });

  it("un general no lo ve", () => {
    montar(USUARIO_GENERAL);
    expect(screen.queryByRole("button", { name: /registrar venta/i })).not.toBeInTheDocument();
  });

  it("muestra quién eres y con qué rol", () => {
    montar(USUARIO_GENERAL);
    expect(screen.getByText("General")).toBeInTheDocument();
    expect(screen.getByText(/solo consulta/i)).toBeInTheDocument();
  });
});

describe("cuenta y tema", () => {
  it("salir cierra la sesión", async () => {
    const { cerrarSesion } = montar(USUARIO_ADMIN);
    await userEvent.click(screen.getByRole("button", { name: /salir/i }));
    expect(cerrarSesion).toHaveBeenCalledOnce();
  });

  it("el interruptor alterna entre oscuro y claro", async () => {
    montar(USUARIO_ADMIN);
    expect(document.documentElement.dataset.tema).toBe("oscuro");
    await userEvent.click(screen.getByRole("button", { name: /cambiar a tema claro/i }));
    expect(document.documentElement.dataset.tema).toBe("claro");
    await userEvent.click(screen.getByRole("button", { name: /cambiar a tema oscuro/i }));
    expect(document.documentElement.dataset.tema).toBe("oscuro");
  });

  it("sin foto de Discord muestra la inicial del nombre", () => {
    montar(USUARIO_ADMIN);
    expect(screen.getByText("J", { selector: "[aria-hidden]" })).toBeInTheDocument();
  });
});
