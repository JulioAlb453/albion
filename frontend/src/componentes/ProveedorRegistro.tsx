import { useCallback, useMemo, useState, type ReactNode } from "react";
import { Cajon } from "../ui/Cajon";
import { ContextoRegistro, type PrefillVenta } from "./ContextoRegistro";
import { FormularioVenta } from "./FormularioVenta";

/** Dueño del formulario de registrar una venta: cualquier pantalla puede abrirlo, con datos cargados. */
export function ProveedorRegistro({ children }: { children: ReactNode }) {
  const [estado, setEstado] = useState<{ abierto: boolean; prefill?: PrefillVenta; clave: number }>({
    abierto: false,
    clave: 0,
  });
  const abrirVenta = useCallback(
    (prefill?: PrefillVenta) => setEstado((actual) => ({ abierto: true, prefill, clave: actual.clave + 1 })),
    [],
  );
  const cerrar = useCallback(() => setEstado((actual) => ({ ...actual, abierto: false })), []);
  const valor = useMemo(() => ({ abrirVenta }), [abrirVenta]);

  return (
    <ContextoRegistro value={valor}>
      {children}
      <Cajon abierto={estado.abierto} titulo="Registrar venta" alCerrar={cerrar}>
        {/* la clave cambia en cada apertura: el formulario siempre empieza limpio */}
        <FormularioVenta key={estado.clave} prefill={estado.prefill} alTerminar={cerrar} />
      </Cajon>
    </ContextoRegistro>
  );
}
