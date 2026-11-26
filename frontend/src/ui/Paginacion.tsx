type Numero = number | "…";

/**
 * Páginas a mostrar: la primera, la última y las vecinas de la actual. Un hueco de una sola
 * página se llena con su número (poner "…" en su lugar no ahorra espacio).
 */
export function numerosDePagina(actual: number, totalPaginas: number): Numero[] {
  const visibles = new Set([1, totalPaginas, actual - 1, actual, actual + 1].filter((n) => n >= 1 && n <= totalPaginas));
  const ordenadas = [...visibles].sort((a, b) => a - b);
  const resultado: Numero[] = [];
  ordenadas.forEach((n, i) => {
    const anterior = ordenadas[i - 1];
    if (anterior !== undefined && n - anterior === 2) resultado.push(anterior + 1);
    else if (anterior !== undefined && n - anterior > 2) resultado.push("…");
    resultado.push(n);
  });
  return resultado;
}

interface Props {
  pagina: number;
  total: number;
  porPagina: number;
  alCambiar: (pagina: number) => void;
}

export function Paginacion({ pagina, total, porPagina, alCambiar }: Props) {
  const totalPaginas = Math.ceil(total / porPagina);
  if (totalPaginas <= 1) return null;
  const desde = (pagina - 1) * porPagina + 1;
  const hasta = Math.min(pagina * porPagina, total);

  return (
    <nav className="paginacion" aria-label="Paginación">
      <span className="texto-2">{desde}–{hasta} de {total}</span>
      <div className="paginacion__botones">
        <button
          type="button" className="boton boton--chico boton--fantasma" aria-label="Página anterior"
          disabled={pagina <= 1} onClick={() => alCambiar(pagina - 1)}
        >
          <span aria-hidden="true">‹</span>
        </button>
        {numerosDePagina(pagina, totalPaginas).map((n, i) =>
          n === "…" ? (
            <span key={`hueco-${i}`} className="paginacion__hueco" aria-hidden="true">…</span>
          ) : (
            <button
              key={n} type="button"
              className={`boton boton--chico ${n === pagina ? "boton--primario" : "boton--fantasma"}`}
              aria-label={`Página ${n}`} aria-current={n === pagina ? "page" : undefined}
              onClick={() => alCambiar(n)}
            >
              {n}
            </button>
          ),
        )}
        <button
          type="button" className="boton boton--chico boton--fantasma" aria-label="Página siguiente"
          disabled={pagina >= totalPaginas} onClick={() => alCambiar(pagina + 1)}
        >
          <span aria-hidden="true">›</span>
        </button>
      </div>
    </nav>
  );
}
