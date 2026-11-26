import type {
  ClienteApi, Comparacion, Gasto, NuevaVenta, NuevoGasto, ObjetoCatalogo, ParametrosComparar,
  PuntoBalance, Reportes, SaldoInicial, UsuarioDiscord, Venta,
} from "./tipos.js";

export class ErrorApi extends Error {
  override name = "ErrorApi";
  constructor(readonly status: number, mensaje: string) {
    super(mensaje);
  }
}

interface Opciones {
  baseUrl: string;
  clave: string;
  fetchFn?: typeof fetch;
  tiempoMs?: number;
}

/** Cada comando crea su cliente con `como(usuario)`: la API decide el rol de quien lo usó. */
export function crearApi({ baseUrl, clave, fetchFn = fetch, tiempoMs = 10_000 }: Opciones) {
  return {
    como(usuario: UsuarioDiscord): ClienteApi {
      const cabeceras = new Headers({
        "x-bot-clave": clave,
        "x-discord-id": usuario.id,
        "x-discord-nombre": encodeURIComponent(usuario.globalName || usuario.username),
      });
      if (usuario.avatar) cabeceras.set("x-discord-avatar", usuario.avatar);

      async function pedir<T>(ruta: string, params: Record<string, string | number | undefined> = {}, cuerpo?: unknown): Promise<T> {
        const url = new URL(baseUrl + ruta);
        for (const [k, v] of Object.entries(params)) if (v !== undefined) url.searchParams.set(k, String(v));
        const h = new Headers(cabeceras);
        if (cuerpo !== undefined) h.set("content-type", "application/json");
        let r: Response;
        try {
          r = await fetchFn(url.toString(), {
            method: cuerpo === undefined ? "GET" : "POST",
            headers: h,
            body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
            signal: AbortSignal.timeout(tiempoMs),
          });
        } catch {
          throw new ErrorApi(0, "No pude conectar con la API del gremio. Inténtalo en un momento.");
        }
        if (!r.ok) throw new ErrorApi(r.status, await mensajeDeError(r));
        return (await r.json()) as T;
      }

      const o404 = async <T>(promesa: Promise<T>, vacio: T): Promise<T> =>
        promesa.catch((e: unknown) => {
          if (e instanceof ErrorApi && e.status === 404) return vacio;
          throw e;
        });

      return {
        buscarObjetos: (q) => pedir<ObjetoCatalogo[]>("/api/catalogo", { q, limite: 25 }),
        obtenerObjeto: (id) => pedir<ObjetoCatalogo>(`/api/catalogo/${encodeURIComponent(id)}`),
        comparar: (p: ParametrosComparar) => pedir<Comparacion[]>("/api/mercado/comparar", { ...p }),
        saldoInicial: () => o404(pedir<SaldoInicial | null>("/api/balance/saldo-inicial"), null),
        evolucion: () => o404(pedir<PuntoBalance[]>("/api/balance/evolucion"), []),
        reportes: (desde) => pedir<Reportes>("/api/reportes", { desde }),
        registrarVenta: (v: NuevaVenta) => pedir<Venta>("/api/ventas", {}, v),
        registrarGasto: (g: NuevoGasto) => pedir<Gasto>("/api/gastos", {}, g),
      };
    },
  };
}

async function mensajeDeError(r: Response): Promise<string> {
  try {
    const { detail } = (await r.json()) as { detail?: unknown };
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d: { loc?: unknown[]; msg?: string }) => `${String(d.loc?.at(-1) ?? "")}: ${d.msg ?? ""}`)
        .join("; ");
    }
  } catch {
    /* sin JSON */
  }
  return `La API respondió con error ${r.status}`;
}
