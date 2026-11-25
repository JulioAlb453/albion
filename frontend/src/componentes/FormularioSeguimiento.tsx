import { useState, type FormEvent } from "react";
import { useCrearSeguimiento } from "../api/consultas";
import { CIUDADES, type Ciudad, type NuevoSeguimiento, type ObjetoCatalogo } from "../api/tipos";
import { useAvisos } from "../ui/Avisos";
import { etiquetaCalidad } from "../util/formato";
import { SelectorObjeto } from "./SelectorObjeto";

interface Props {
  prefill?: { objeto?: ObjetoCatalogo; encantamiento?: number; calidad?: number };
  alTerminar: () => void;
}

/** Vigilar un objeto: la app revisa sus precios y avisa cuando conviene venderlo en otra ciudad. */
export function FormularioSeguimiento({ prefill, alTerminar }: Props) {
  const [objeto, setObjeto] = useState<ObjetoCatalogo | null>(prefill?.objeto ?? null);
  const [encantamiento, setEncantamiento] = useState(prefill?.encantamiento ?? 0);
  const [calidad, setCalidad] = useState(prefill?.calidad ?? 1);
  const [referencia, setReferencia] = useState<Ciudad>("Fort Sterling");
  const [porcentaje, setPorcentaje] = useState("");
  const [neto, setNeto] = useState("");
  const crear = useCrearSeguimiento();
  const { avisar } = useAvisos();

  const porcentajeValido = porcentaje !== "" && Number(porcentaje) > 0;
  const netoValido = neto !== "" && Number.isInteger(Number(neto)) && Number(neto) > 0;
  const sinErrores = (porcentaje === "" || porcentajeValido) && (neto === "" || netoValido);
  const valido = objeto !== null && (porcentajeValido || netoValido) && sinErrores;

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    if (!objeto || !valido) return;
    const seguimiento: NuevoSeguimiento = {
      base_id: objeto.base_id,
      encantamiento: objeto.tiene_calidad ? encantamiento : 0,
      calidad: objeto.tiene_calidad ? calidad : 1,
      ciudad_referencia: referencia,
      ...(porcentajeValido ? { porcentaje_minimo: Number(porcentaje) } : {}),
      ...(netoValido ? { neto_minimo: Number(neto) } : {}),
    };
    crear.mutate(seguimiento, {
      onSuccess: () => {
        avisar(`Ahora vigilas ${objeto.nombre}`, "exito");
        alTerminar();
      },
    });
  };

  return (
    <form className="formulario" onSubmit={enviar}>
      <div className="campo">
        <span>Objeto</span>
        <SelectorObjeto
          valor={objeto}
          alElegir={(elegido) => {
            setObjeto(elegido);
            setEncantamiento(0);
            setCalidad(1);
          }}
        />
      </div>

      {objeto?.tiene_calidad && (
        <div className="rejilla-2">
          <label className="campo">
            <span>Encantamiento</span>
            <select value={encantamiento} onChange={(e) => setEncantamiento(Number(e.target.value))}>
              {[0, 1, 2, 3, 4].map((n) => <option key={n} value={n}>{n === 0 ? ".0 (sin encantar)" : `.${n}`}</option>)}
            </select>
          </label>
          <label className="campo">
            <span>Calidad</span>
            <select value={calidad} onChange={(e) => setCalidad(Number(e.target.value))}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{etiquetaCalidad(n)}</option>)}
            </select>
          </label>
        </div>
      )}

      <label className="campo">
        <span>Ciudad de referencia</span>
        <select value={referencia} onChange={(e) => setReferencia(e.target.value as Ciudad)}>
          {CIUDADES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <span className="campo__ayuda">Con la que se compara. Normalmente, donde ya vendías: tu isla principal.</span>
      </label>

      <fieldset className="opciones">
        <legend>Avísame cuando…</legend>
        <label className="campo">
          <span>Otra ciudad pague este % más neto que la de referencia</span>
          <input type="number" min={0.1} step={0.1} placeholder="15" value={porcentaje} onChange={(e) => setPorcentaje(e.target.value)} />
        </label>
        <label className="campo">
          <span>El neto por unidad llega a (plata)</span>
          <input type="number" min={1} step={1} inputMode="numeric" placeholder="300000" value={neto} onChange={(e) => setNeto(e.target.value)} />
        </label>
        <p className="campo__ayuda">Elige al menos una. Los datos de más de 6 horas nunca disparan una alerta.</p>
      </fieldset>

      {crear.isError && <p role="alert" className="caja caja--error">{crear.error.message}</p>}

      <div>
        <button type="submit" className="boton boton--primario boton--grande" disabled={!valido || crear.isPending}>
          {crear.isPending ? "Guardando…" : "Vigilar objeto"}
        </button>
      </div>
    </form>
  );
}
