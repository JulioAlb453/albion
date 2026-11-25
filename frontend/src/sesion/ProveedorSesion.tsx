import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo, useState, type ReactNode } from "react";
import { ProveedorApi } from "../api/ContextoApi";
import { crearCliente } from "../api/cliente";
import type { Usuario } from "../api/tipos";
import { URL_API } from "../config";
import { Entrar } from "../paginas/Entrar";
import { ContextoSesion } from "./ContextoSesion";
import { borrarToken, leerToken } from "./sesion";

/** Decide qué se ve: la entrada con Discord, una espera, un fallo de conexión o la aplicación. */
export function ProveedorSesion({ children, errorInicial }: { children: ReactNode; errorInicial?: string }) {
  const consultas = useQueryClient();
  const [hayToken, setHayToken] = useState(() => leerToken() !== null);
  const [aviso, setAviso] = useState<string | undefined>(errorInicial);

  const cerrar = useCallback(
    (motivo?: string) => {
      borrarToken();
      setHayToken(false);
      setAviso(motivo);
      consultas.clear();
    },
    [consultas],
  );

  const cliente = useMemo(
    () => crearCliente({ baseUrl: URL_API, obtenerToken: leerToken, alSesionVencida: () => cerrar("sesion_vencida") }),
    [cerrar],
  );

  const yo = useQuery({
    queryKey: ["yo"],
    queryFn: () => cliente.get<Usuario>("/api/auth/yo"),
    enabled: hayToken,
    retry: false,
    staleTime: Infinity,
  });

  if (!hayToken) return <Entrar error={aviso} />;
  if (yo.isError) {
    return (
      <main className="entrada">
        <section className="bloque entrada__tarjeta">
          <h1>Sin conexión con la API</h1>
          <p className="texto-2" role="status">{yo.error.message}</p>
          <div className="fila">
            <button className="boton boton--primario" onClick={() => void yo.refetch()}>Reintentar</button>
            <button className="boton" onClick={() => cerrar()}>Salir</button>
          </div>
        </section>
      </main>
    );
  }
  if (!yo.data) {
    return (
      <main className="entrada">
        <p className="texto-2" role="status">Cargando…</p>
      </main>
    );
  }

  return (
    <ProveedorApi value={cliente}>
      <ContextoSesion value={{ usuario: yo.data, cerrarSesion: () => cerrar() }}>{children}</ContextoSesion>
    </ProveedorApi>
  );
}
