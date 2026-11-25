import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { conReactQuery, json, jwtDeEjemplo, USUARIO_ADMIN } from "../pruebas/utiles";
import { useSesion } from "./ContextoSesion";
import { ProveedorSesion } from "./ProveedorSesion";
import { guardarToken, leerToken } from "./sesion";

function Contenido() {
  const { usuario, cerrarSesion } = useSesion();
  return (
    <>
      <p>Hola {usuario.nombre}</p>
      <button onClick={cerrarSesion}>Salir</button>
    </>
  );
}

function montar(errorInicial?: string) {
  return conReactQuery(
    <ProveedorSesion errorInicial={errorInicial}>
      <Contenido />
    </ProveedorSesion>,
  );
}

const fetchFalso = vi.fn<typeof fetch>();
beforeEach(() => {
  fetchFalso.mockReset();
  vi.stubGlobal("fetch", fetchFalso);
});
afterEach(() => vi.unstubAllGlobals());

describe("sin sesión", () => {
  it("muestra la entrada con Discord y no llama a la API", () => {
    montar();
    const enlace = screen.getByRole("link", { name: /entrar con discord/i });
    expect(enlace).toHaveAttribute("href", "http://localhost:8000/api/auth/discord/login");
    expect(fetchFalso).not.toHaveBeenCalled();
  });

  it.each([
    ["sin_acceso", /no tiene un rol del gremio/i],
    ["cancelado", /cancelaste/i],
    ["estado_invalido", /expiró/i],
    ["codigo_invalido", /rechazó el código/i],
    ["discord_no_disponible", /no se pudo hablar con discord/i],
    ["algo_raro", /algo_raro/],
  ])("traduce el error %s del regreso de Discord", (codigo, texto) => {
    montar(codigo);
    expect(screen.getByRole("alert")).toHaveTextContent(texto);
  });

  it("explica que no se lee el correo ni la contraseña", () => {
    montar();
    expect(screen.getByText(/no vemos tu correo ni tu contraseña/i)).toBeInTheDocument();
  });
});

describe("con sesión", () => {
  it("carga al usuario con su token y muestra la aplicación", async () => {
    const token = jwtDeEjemplo();
    guardarToken(token);
    fetchFalso.mockResolvedValue(json(USUARIO_ADMIN));
    montar();
    expect(await screen.findByText("Hola Julio")).toBeInTheDocument();
    const [url, opciones] = fetchFalso.mock.calls[0]!;
    expect(String(url)).toBe("http://localhost:8000/api/auth/yo");
    expect(new Headers(opciones?.headers).get("authorization")).toBe(`Bearer ${token}`);
  });

  it("si la API responde 401 vuelve a la entrada y avisa que la sesión venció", async () => {
    guardarToken(jwtDeEjemplo());
    fetchFalso.mockResolvedValue(json({ detail: "La sesión expiró" }, 401));
    montar();
    expect(await screen.findByRole("alert")).toHaveTextContent(/sesión venció/i);
    expect(leerToken()).toBeNull();
  });

  it("si no hay conexión ofrece reintentar sin perder la sesión", async () => {
    guardarToken(jwtDeEjemplo());
    fetchFalso.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    montar();
    expect(await screen.findByText(/no se pudo conectar/i)).toBeInTheDocument();
    expect(leerToken()).not.toBeNull();

    fetchFalso.mockResolvedValue(json(USUARIO_ADMIN));
    await userEvent.click(screen.getByRole("button", { name: /reintentar/i }));
    expect(await screen.findByText("Hola Julio")).toBeInTheDocument();
  });

  it("cerrar sesión borra el token y vuelve a la entrada", async () => {
    guardarToken(jwtDeEjemplo());
    fetchFalso.mockResolvedValue(json(USUARIO_ADMIN));
    montar();
    await userEvent.click(await screen.findByRole("button", { name: "Salir" }));
    await waitFor(() => expect(screen.getByRole("link", { name: /entrar con discord/i })).toBeInTheDocument());
    expect(leerToken()).toBeNull();
  });
});
