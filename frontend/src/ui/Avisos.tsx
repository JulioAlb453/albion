import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { Icono } from "./Icono";

type Tipo = "info" | "exito" | "error";
interface Aviso {
  id: number;
  texto: string;
  tipo: Tipo;
}

const ContextoAvisos = createContext<{ avisar: (texto: string, tipo?: Tipo) => void } | null>(null);

export function ProveedorAvisos({ children }: { children: ReactNode }) {
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const contador = useRef(0);

  const quitar = useCallback((id: number) => setAvisos((actuales) => actuales.filter((a) => a.id !== id)), []);
  const avisar = useCallback(
    (texto: string, tipo: Tipo = "info") => {
      const id = ++contador.current;
      setAvisos((actuales) => [...actuales, { id, texto, tipo }]);
      setTimeout(() => quitar(id), tipo === "error" ? 9_000 : 5_000);
    },
    [quitar],
  );
  const valor = useMemo(() => ({ avisar }), [avisar]);

  return (
    <ContextoAvisos value={valor}>
      {children}
      <div className="avisos">
        {avisos.map(({ id, texto, tipo }) => (
          <div key={id} className={`aviso aviso--${tipo}`} role={tipo === "error" ? "alert" : "status"}>
            <span>{texto}</span>
            <button className="boton boton--fantasma boton--icono" aria-label="Cerrar aviso" onClick={() => quitar(id)}>
              <Icono nombre="cerrar" tamano={16} />
            </button>
          </div>
        ))}
      </div>
    </ContextoAvisos>
  );
}

export function useAvisos() {
  const valor = useContext(ContextoAvisos);
  if (!valor) throw new Error("useAvisos se usó fuera de ProveedorAvisos");
  return valor;
}
