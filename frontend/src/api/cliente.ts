export interface ErrorFila {
  fila: number;
  mensaje: string;
}

/** Un fallo de la API ya traducido a algo que se le puede mostrar a la persona. */
export class ErrorApi extends Error {
  readonly status: number;
  /** Solo en importaciones rechazadas: cada fila mala con su motivo. */
  readonly errores?: ErrorFila[];

  constructor(status: number, mensaje: string, errores?: ErrorFila[]) {
    super(mensaje);
    this.name = "ErrorApi";
    this.status = status;
    this.errores = errores;
  }
}

export type Parametros = Record<string, string | number | boolean | null | undefined>;

interface Opciones {
  baseUrl: string;
  obtenerToken: () => string | null;
  /** La API respondió 401: el token venció o ya no vale. */
  alSesionVencida: () => void;
  fetchFn?: typeof fetch;
}

interface Extras {
  params?: Parametros;
  cuerpo?: unknown;
  formulario?: FormData;
}

export function crearCliente(opciones: Opciones) {
  const llamar = opciones.fetchFn ?? ((...args: Parameters<typeof fetch>) => fetch(...args));

  function direccion(ruta: string, params?: Parametros): string {
    const url = new URL(ruta, opciones.baseUrl);
    for (const [clave, valor] of Object.entries(params ?? {})) {
      if (valor !== undefined && valor !== null && valor !== "") url.searchParams.set(clave, String(valor));
    }
    return url.toString();
  }

  async function aError(respuesta: Response): Promise<ErrorApi> {
    let cuerpo: { detail?: unknown; errores?: unknown } | null = null;
    try {
      cuerpo = await respuesta.json();
    } catch {
      // la respuesta no era JSON (por ejemplo, la página de error de un proxy)
    }
    if (respuesta.status === 401) opciones.alSesionVencida();

    const errores = Array.isArray(cuerpo?.errores) ? (cuerpo.errores as ErrorFila[]) : undefined;
    const detalle = cuerpo?.detail;
    let mensaje: string;
    if (errores) {
      mensaje = `El archivo tiene ${errores.length} fila${errores.length === 1 ? "" : "s"} con problemas`;
    } else if (typeof detalle === "string") {
      mensaje = detalle;
    } else if (Array.isArray(detalle)) {
      mensaje = detalle
        .map((e: { loc?: unknown[]; msg?: string }) => {
          const campo = e.loc?.at(-1);
          return campo === undefined ? String(e.msg) : `${String(campo)}: ${e.msg}`;
        })
        .join("; ");
    } else {
      mensaje = `El servidor respondió ${respuesta.status}`;
    }
    return new ErrorApi(respuesta.status, mensaje, errores);
  }

  async function enviar(metodo: string, ruta: string, { params, cuerpo, formulario }: Extras = {}) {
    // El dominio gratuito de ngrok responde una página HTML de aviso a las peticiones de un
    // navegador, salvo que lleve esta cabecera (cualquier valor). En otros servidores no hace nada.
    const cabeceras = new Headers({ "ngrok-skip-browser-warning": "true" });
    const token = opciones.obtenerToken();
    if (token) cabeceras.set("Authorization", `Bearer ${token}`);

    let body: BodyInit | undefined;
    if (formulario) {
      body = formulario; // el navegador agrega el tipo y el límite del formulario
    } else if (cuerpo !== undefined) {
      cabeceras.set("Content-Type", "application/json");
      body = JSON.stringify(cuerpo);
    }

    let respuesta: Response;
    try {
      respuesta = await llamar(direccion(ruta, params), { method: metodo, headers: cabeceras, body });
    } catch {
      throw new ErrorApi(0, "No se pudo conectar con el servidor. Revisa que tu PC y la API estén encendidas.");
    }
    if (!respuesta.ok) throw await aError(respuesta);
    return respuesta;
  }

  async function json<T>(respuesta: Response): Promise<T> {
    return respuesta.status === 204 ? (undefined as T) : ((await respuesta.json()) as T);
  }

  return {
    get: <T>(ruta: string, params?: Parametros) => enviar("GET", ruta, { params }).then((r) => json<T>(r)),
    post: <T>(ruta: string, cuerpo?: unknown) => enviar("POST", ruta, { cuerpo }).then((r) => json<T>(r)),
    put: <T>(ruta: string, cuerpo?: unknown) => enviar("PUT", ruta, { cuerpo }).then((r) => json<T>(r)),
    delete: <T = void>(ruta: string) => enviar("DELETE", ruta).then((r) => json<T>(r)),

    subir<T>(ruta: string, archivo: File, campo = "archivo") {
      const formulario = new FormData();
      formulario.append(campo, archivo, archivo.name);
      return enviar("POST", ruta, { formulario }).then((r) => json<T>(r));
    },

    async descargar(ruta: string, params?: Parametros): Promise<{ archivo: Blob; nombre: string }> {
      const respuesta = await enviar("GET", ruta, { params });
      const nombre = /filename="?([^";]+)"?/.exec(respuesta.headers.get("content-disposition") ?? "")?.[1];
      return { archivo: await respuesta.blob(), nombre: nombre ?? "descarga" };
    },
  };
}

export type Cliente = ReturnType<typeof crearCliente>;
