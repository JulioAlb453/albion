import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { ProveedorApi } from "../api/ContextoApi";
import { crearCliente } from "../api/cliente";
import type { Usuario } from "../api/tipos";
import { ContextoRegistro, type ValorRegistro } from "../componentes/ContextoRegistro";
import { URL_API } from "../config";
import { ContextoSesion } from "../sesion/ContextoSesion";
import { ProveedorAvisos } from "../ui/Avisos";
import { guardarArchivo } from "../util/descargar";

/** Un JWT con la forma real; solo importa la fecha de vencimiento. */
export function jwtDeEjemplo(horas = 1): string {
  const b64 = (o: object) => btoa(JSON.stringify(o)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return `${b64({ alg: "HS256" })}.${b64({ sub: "1", exp: Math.floor(Date.now() / 1000) + horas * 3600 })}.firma`;
}

export function json(cuerpo: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(cuerpo), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function clienteDePruebas(): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } } });
}

export function conReactQuery(ui: ReactElement, cliente = clienteDePruebas()) {
  return render(<QueryClientProvider client={cliente}>{ui}</QueryClientProvider>);
}

export const USUARIO_ADMIN: Usuario = {
  discord_id: "1", nombre: "Julio", avatar_hash: null, rol: "admin", puede_registrar: true,
};
export const USUARIO_GENERAL: Usuario = {
  discord_id: "2", nombre: "General", avatar_hash: null, rol: "general", puede_registrar: false,
};

/**
 * Lo último que se mandó a guardar como archivo (en las pruebas que reemplazan `guardarArchivo`).
 * Se mira el contenido y no la clase del Blob: según la versión de Node, el de la respuesta y el
 * de jsdom son clases distintas aunque se comporten igual.
 */
export async function ultimaDescarga(): Promise<{ nombre: string; contenido: string }> {
  const [archivo, nombre] = vi.mocked(guardarArchivo).mock.calls.at(-1)!;
  return { nombre, contenido: await archivo.text() };
}

export interface Llamada {
  metodo: string;
  ruta: string;
  params: Record<string, string>;
  cuerpo: unknown;
}
/** Un valor (se responde con él como JSON), una función que lo calcula, o directamente una Response. */
type Manejador = unknown;

/**
 * Reemplaza `fetch` por una API de mentira. Las rutas se escriben "GET /api/ventas".
 * Devuelve la lista de llamadas, que se va llenando, para comprobar qué se pidió.
 */
export function instalarApi(rutas: Record<string, Manejador>): Llamada[] {
  const llamadas: Llamada[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, opciones?: RequestInit) => {
      const direccion = new URL(url);
      const metodo = opciones?.method ?? "GET";
      let cuerpo: unknown;
      if (typeof opciones?.body === "string") cuerpo = JSON.parse(opciones.body);
      else if (opciones?.body instanceof FormData) cuerpo = opciones.body;
      const llamada: Llamada = { metodo, ruta: direccion.pathname, params: Object.fromEntries(direccion.searchParams), cuerpo };
      llamadas.push(llamada);

      const manejador = rutas[`${metodo} ${direccion.pathname}`];
      if (manejador === undefined) return json({ detail: `Sin ruta falsa para ${metodo} ${direccion.pathname}` }, 404);
      const resultado = typeof manejador === "function" ? (manejador as (l: Llamada) => unknown)(llamada) : manejador;
      return resultado instanceof Response ? resultado : json(resultado);
    }),
  );
  return llamadas;
}

interface OpcionesPagina {
  usuario?: Usuario;
  ruta?: string;
  registro?: Partial<ValorRegistro>;
}

/** Monta una página con todo lo que necesita: consultas, API, sesión, avisos y rutas. */
export function montarPagina(ui: ReactElement, { usuario = USUARIO_ADMIN, ruta = "/", registro }: OpcionesPagina = {}) {
  const cliente = crearCliente({ baseUrl: URL_API, obtenerToken: () => "token-de-prueba", alSesionVencida: () => {} });
  const valorRegistro: ValorRegistro = { abrirVenta: () => {}, ...registro };
  return render(
    <QueryClientProvider client={clienteDePruebas()}>
      <ProveedorApi value={cliente}>
        <ContextoSesion value={{ usuario, cerrarSesion: () => {} }}>
          <ContextoRegistro value={valorRegistro}>
            <ProveedorAvisos>
              <MemoryRouter initialEntries={[ruta]}>{ui}</MemoryRouter>
            </ProveedorAvisos>
          </ContextoRegistro>
        </ContextoSesion>
      </ProveedorApi>
    </QueryClientProvider>,
  );
}
