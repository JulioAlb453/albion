import { useEffect, useState } from "react";

/** El valor, pero solo después de que deje de cambiar durante `ms`: para no buscar con cada tecla. */
export function useRetraso<T>(valor: T, ms: number): T {
  const [retrasado, setRetrasado] = useState(valor);
  useEffect(() => {
    const temporizador = setTimeout(() => setRetrasado(valor), ms);
    return () => clearTimeout(temporizador);
  }, [valor, ms]);
  return retrasado;
}
