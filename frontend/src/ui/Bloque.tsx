import type { ReactNode } from "react";
import { plataCompleta, plataCorta } from "../util/formato";

interface PropsBloque {
  titulo?: string;
  accion?: ReactNode;
  /** Cuántas de las 12 columnas ocupa en pantallas grandes; en las chicas se acomoda solo. */
  columnas?: 3 | 4 | 5 | 6 | 7 | 8 | 9 | 12;
  /** 2 lo hace el doble de alto. */
  filas?: 2;
  acento?: boolean;
  className?: string;
  children: ReactNode;
}

/** Un bloque del Bento Grid. */
export function Bloque({ titulo, accion, columnas, filas, acento, className, children }: PropsBloque) {
  const clases = [
    "bloque",
    columnas && `c-${columnas}`,
    filas && `f-${filas}`,
    acento && "bloque--acento",
    className,
  ].filter(Boolean).join(" ");
  return (
    <section className={clases}>
      {(titulo || accion) && (
        <header className="bloque__cabecera">
          {titulo ? <h2 className="bloque__titulo">{titulo}</h2> : <span />}
          {accion}
        </header>
      )}
      {children}
    </section>
  );
}

/** Plata abreviada (120.6 M); el valor exacto sale al pasar el cursor. */
export function Plata({ valor, tamano, conTono }: { valor: number; tamano?: "media" | "chica"; conTono?: boolean }) {
  const tono = conTono ? (valor > 0 ? " positivo" : valor < 0 ? " negativo" : "") : "";
  return (
    <span className={`cifra${tamano ? ` cifra--${tamano}` : ""}${tono}`} title={plataCompleta(valor)}>
      {plataCorta(valor)}
    </span>
  );
}

export function Insignia({ tono, children }: { tono?: "acento" | "positivo" | "negativo" | "aviso" | "info"; children: ReactNode }) {
  return <span className={`insignia${tono ? ` insignia--${tono}` : ""}`}>{children}</span>;
}

export function Vacio({ titulo, children, accion }: { titulo: string; children?: ReactNode; accion?: ReactNode }) {
  return (
    <div className="vacio">
      <p className="vacio__titulo">{titulo}</p>
      {children && <p className="texto-2">{children}</p>}
      {accion}
    </div>
  );
}
