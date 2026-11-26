import type { ObjetoCatalogo } from "../api/tipos";
import { etiquetaCalidad } from "../util/formato";

/** Lleva encantamiento y calidad a lo que admite el objeto (un tomo no tiene calidad, un recurso .2 es siempre .2). */
export function ajustar(objeto: ObjetoCatalogo, encantamiento: number, calidad: number) {
  return {
    encantamiento: Math.min(Math.max(encantamiento, objeto.encantamiento_min), objeto.encantamiento_max),
    calidad: objeto.tiene_calidad ? calidad : 1,
  };
}

const eligeEncantamiento = (o: ObjetoCatalogo) => o.encantamiento_max > o.encantamiento_min;

/** Si el objeto deja elegir algo: para no dibujar un recuadro vacío. */
export const admiteOpciones = (o: ObjetoCatalogo) => o.tiene_calidad || eligeEncantamiento(o);

interface Props {
  objeto: ObjetoCatalogo;
  encantamiento: number;
  calidad: number;
  alCambiarEncantamiento: (valor: number) => void;
  alCambiarCalidad: (valor: number) => void;
}

/** Los selectores de encantamiento y calidad, solo con lo que el objeto admite. */
export function CamposObjeto({ objeto, encantamiento, calidad, alCambiarEncantamiento, alCambiarCalidad }: Props) {
  const niveles = Array.from(
    { length: objeto.encantamiento_max - objeto.encantamiento_min + 1 },
    (_, i) => objeto.encantamiento_min + i,
  );
  return (
    <>
      {eligeEncantamiento(objeto) && (
        <label className="campo">
          <span>Encantamiento</span>
          <select value={encantamiento} onChange={(e) => alCambiarEncantamiento(Number(e.target.value))}>
            {niveles.map((n) => (
              <option key={n} value={n}>{n === 0 ? ".0 (sin encantar)" : `.${n}`}</option>
            ))}
          </select>
        </label>
      )}
      {objeto.tiene_calidad && (
        <label className="campo">
          <span>Calidad</span>
          <select value={calidad} onChange={(e) => alCambiarCalidad(Number(e.target.value))}>
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>{etiquetaCalidad(n)}</option>
            ))}
          </select>
        </label>
      )}
    </>
  );
}
