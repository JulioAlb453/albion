import { useId, useState, type KeyboardEvent } from "react";
import { useCatalogo } from "../api/consultas";
import { CATEGORIAS_OBJETO, type ObjetoCatalogo } from "../api/tipos";
import { ImagenObjeto } from "../ui/ImagenObjeto";
import { useRetraso } from "../util/useRetraso";

interface Props {
  valor: ObjetoCatalogo | null;
  alElegir: (objeto: ObjetoCatalogo | null) => void;
  etiqueta?: string;
  /** Para que la imagen del objeto elegido refleje lo que se está consultando. */
  encantamiento?: number;
  calidad?: number;
  /** La barra de búsqueda queda siempre a la vista, también con un objeto elegido (sin «Cambiar»). */
  buscarSiempre?: boolean;
}

/** Buscador de objetos del catálogo, con lista desplegable y manejo por teclado. */
export function SelectorObjeto({ valor, alElegir, etiqueta = "Buscar objeto", encantamiento = 0, calidad = 1, buscarSiempre = false }: Props) {
  const [texto, setTexto] = useState("");
  const [abierto, setAbierto] = useState(false);
  const [activo, setActivo] = useState(-1);
  const idLista = useId();
  const buscado = useRetraso(texto.trim(), 250);
  const resultados = useCatalogo(buscado);

  const tarjeta = (elegido: ObjetoCatalogo, conCambiar: boolean) => (
      <div className="selector selector--elegido">
        <ImagenObjeto baseId={elegido.base_id} encantamiento={encantamiento} calidad={calidad} tamano={64} />
        <div className="lista__principal">
          <div className="lista__titulo">{elegido.nombre}</div>
          <div className="lista__detalle">{elegido.base_id}</div>
        </div>
        {conCambiar && <button type="button" className="boton" onClick={() => alElegir(null)}>Cambiar</button>}
      </div>
  );

  if (valor && !buscarSiempre) return tarjeta(valor, true);

  const lista = buscado.length >= 2 ? (resultados.data ?? []) : [];
  const hayLista = abierto && lista.length > 0;
  const sinResultados = abierto && buscado.length >= 2 && resultados.isSuccess && lista.length === 0;

  const elegir = (objeto: ObjetoCatalogo) => {
    setTexto("");
    setAbierto(false);
    setActivo(-1);
    alElegir(objeto);
  };

  const alTeclear = (evento: KeyboardEvent<HTMLInputElement>) => {
    if (evento.key === "ArrowDown") {
      evento.preventDefault();
      setAbierto(true);
      setActivo((i) => Math.min(i + 1, lista.length - 1));
    } else if (evento.key === "ArrowUp") {
      evento.preventDefault();
      setActivo((i) => Math.max(i - 1, 0));
    } else if (evento.key === "Enter" && hayLista && lista[activo]) {
      evento.preventDefault();
      elegir(lista[activo]);
    } else if (evento.key === "Escape") {
      setAbierto(false);
    }
  };

  const busqueda = (
    <div className="selector">
      <input
        role="combobox"
        aria-label={etiqueta}
        aria-expanded={hayLista}
        aria-controls={idLista}
        aria-autocomplete="list"
        aria-activedescendant={hayLista && activo >= 0 ? `${idLista}-${activo}` : undefined}
        autoComplete="off"
        placeholder="Busca por nombre: espada, armadura, hueso…"
        value={texto}
        onChange={(evento) => {
          setTexto(evento.target.value);
          setAbierto(true);
          setActivo(-1);
        }}
        onFocus={() => setAbierto(true)}
        onBlur={() => setAbierto(false)}
        onKeyDown={alTeclear}
      />
      {texto.trim().length === 1 && <p className="campo__ayuda">Escribe al menos 2 letras.</p>}
      {sinResultados && <p className="campo__ayuda" role="status">Sin resultados para «{buscado}».</p>}
      {hayLista && (
        <ul className="selector__lista" role="listbox" id={idLista} aria-label="Resultados">
          {lista.map((objeto, indice) => (
            <li
              key={objeto.base_id}
              id={`${idLista}-${indice}`}
              role="option"
              aria-selected={indice === activo}
              className="selector__opcion"
              // mousedown (y no click): se elige antes de que el campo pierda el foco y cierre la lista
              onMouseDown={(evento) => {
                evento.preventDefault();
                elegir(objeto);
              }}
            >
              <ImagenObjeto baseId={objeto.base_id} tamano={36} />
              <span className="selector__texto">
                <span className="lista__titulo">{objeto.nombre}</span>
                <span className="lista__detalle">{objeto.base_id} · {CATEGORIAS_OBJETO[objeto.categoria]}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  if (!valor) return busqueda;
  return (
    <div className="selector-fijo">
      {busqueda}
      {tarjeta(valor, false)}
    </div>
  );
}
