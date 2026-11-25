import { useState } from "react";
import { BloqueAlertas, BloqueOportunidades, BloqueUltimasVentas } from "../componentes/panel/BloquesActividad";
import { BloqueImpuestosGastos, BloqueResumen, BloqueSaldo } from "../componentes/panel/BloquesFinanzas";
import { diaLocalHaceDias, inicioDelDia } from "../util/formato";

const PERIODOS = [
  { valor: "7", texto: "7 días" },
  { valor: "30", texto: "30 días" },
  { valor: "todo", texto: "Todo" },
] as const;

export function Panel() {
  const [periodo, setPeriodo] = useState<(typeof PERIODOS)[number]["valor"]>("30");
  const dias = periodo === "todo" ? null : Number(periodo);
  const desde = dias === null ? undefined : inicioDelDia(diaLocalHaceDias(dias));

  return (
    <div className="pila pila--grande">
      <div className="chips" role="group" aria-label="Periodo">
        {PERIODOS.map(({ valor, texto }) => (
          <button key={valor} type="button" className="chip" aria-pressed={periodo === valor} onClick={() => setPeriodo(valor)}>
            {texto}
          </button>
        ))}
      </div>
      <div className="bento">
        <BloqueSaldo dias={dias} />
        <BloqueResumen desde={desde} />
        <BloqueImpuestosGastos desde={desde} />
        <BloqueOportunidades />
        <BloqueAlertas />
        <BloqueUltimasVentas />
      </div>
    </div>
  );
}
