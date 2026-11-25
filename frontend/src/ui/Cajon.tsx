import { useEffect, useId, useRef, type ReactNode } from "react";
import { Icono } from "./Icono";

interface Props {
  abierto: boolean;
  titulo: string;
  alCerrar: () => void;
  children: ReactNode;
}

/** Panel que entra por la derecha, para formularios que no merecen una página propia. */
export function Cajon({ abierto, titulo, alCerrar, children }: Props) {
  const dialogo = useRef<HTMLDivElement>(null);
  const idTitulo = useId();
  // El padre crea una función nueva en cada render: se guarda aparte para que el efecto de
  // abajo no se repita (y no le quite el foco a quien está escribiendo).
  const cerrar = useRef(alCerrar);
  useEffect(() => {
    cerrar.current = alCerrar;
  });

  useEffect(() => {
    if (!abierto) return;
    const anterior = document.activeElement as HTMLElement | null;
    const primero = dialogo.current?.querySelector<HTMLElement>("input, select, textarea");
    (primero ?? dialogo.current)?.focus();
    const alTeclear = (evento: KeyboardEvent) => {
      if (evento.key === "Escape") cerrar.current();
    };
    document.addEventListener("keydown", alTeclear);
    return () => {
      document.removeEventListener("keydown", alTeclear);
      anterior?.focus();
    };
  }, [abierto]);

  if (!abierto) return null;
  return (
    <div
      className="cajon-fondo"
      data-testid="cajon-fondo"
      // Al presionar, no al soltar: arrastrar para seleccionar texto desde dentro hasta fuera no lo cierra.
      onMouseDown={(evento) => {
        if (evento.target === evento.currentTarget) cerrar.current();
      }}
    >
      <div ref={dialogo} className="cajon" role="dialog" aria-modal="true" aria-labelledby={idTitulo} tabIndex={-1}>
        <header className="cajon__cabecera">
          <h2 id={idTitulo} className="cajon__titulo">{titulo}</h2>
          <button className="boton boton--fantasma boton--icono" aria-label="Cerrar" onClick={() => cerrar.current()}>
            <Icono nombre="cerrar" />
          </button>
        </header>
        <div className="cajon__cuerpo">{children}</div>
      </div>
    </div>
  );
}
