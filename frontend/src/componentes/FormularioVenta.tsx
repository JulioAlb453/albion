import { useState, type FormEvent } from "react";
import { useRegistrarVenta } from "../api/consultas";
import { CIUDADES, TIPOS_VENTA, type Ciudad, type NuevaVenta, type ObjetoCatalogo, type TipoVenta } from "../api/tipos";
import { useAvisos } from "../ui/Avisos";
import { calcularDesglose } from "../util/desglose";
import { plataCompleta } from "../util/formato";
import type { PrefillVenta } from "./ContextoRegistro";
import { admiteOpciones, ajustar, CamposObjeto } from "./CamposObjeto";
import { SelectorObjeto } from "./SelectorObjeto";

interface Props {
  prefill?: PrefillVenta;
  alTerminar: () => void;
}

const enteroPositivo = (texto: string) => texto !== "" && Number.isInteger(Number(texto)) && Number(texto) > 0;

/** Registra una venta, con el desglose de impuestos a la vista antes de guardar. */
export function FormularioVenta({ prefill, alTerminar }: Props) {
  const [objeto, setObjeto] = useState<ObjetoCatalogo | null>(prefill?.objeto ?? null);
  const [encantamiento, setEncantamiento] = useState(prefill?.encantamiento ?? 0);
  const [calidad, setCalidad] = useState(prefill?.calidad ?? 1);
  const [ciudad, setCiudad] = useState<Ciudad>(prefill?.ciudad ?? "Fort Sterling");
  const [tipo, setTipo] = useState<TipoVenta>(prefill?.tipo ?? "directa");
  const [cantidad, setCantidad] = useState(String(prefill?.cantidad ?? 1));
  const [precio, setPrecio] = useState(prefill?.precio_unitario ? String(prefill.precio_unitario) : "");
  const [tarifaExtra, setTarifaExtra] = useState("");
  const [fecha, setFecha] = useState("");
  const registrar = useRegistrarVenta();
  const { avisar } = useAvisos();

  const extra = tipo === "orden" && Number(tarifaExtra) > 0 ? Number(tarifaExtra) : 0;
  const valido = objeto !== null && enteroPositivo(precio) && enteroPositivo(cantidad);
  const desglose = enteroPositivo(precio) && enteroPositivo(cantidad)
    ? calcularDesglose(Number(precio), Number(cantidad), tipo, extra)
    : null;


  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    if (!objeto || !valido) return;
    const venta: NuevaVenta = {
      base_id: objeto.base_id,
      ...ajustar(objeto, encantamiento, calidad),
      ciudad,
      tipo,
      cantidad: Number(cantidad),
      precio_unitario: Number(precio),
      ...(fecha ? { fecha: new Date(fecha).toISOString() } : {}),
      ...(extra > 0 ? { tarifa_extra: extra } : {}),
    };
    registrar.mutate(venta, {
      onSuccess: () => {
        avisar("Venta registrada", "exito");
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
            setEncantamiento(elegido?.encantamiento_min ?? 0);
            setCalidad(1);
          }}
        />
      </div>

      {objeto && admiteOpciones(objeto) && (
        <div className="rejilla-2">
          <CamposObjeto
            objeto={objeto} encantamiento={encantamiento} calidad={calidad}
            alCambiarEncantamiento={setEncantamiento} alCambiarCalidad={setCalidad}
          />
        </div>
      )}

      <label className="campo">
        <span>Ciudad</span>
        <select value={ciudad} onChange={(e) => setCiudad(e.target.value as Ciudad)}>
          {CIUDADES.map((nombre) => (
            <option key={nombre} value={nombre}>{nombre}</option>
          ))}
        </select>
      </label>

      <fieldset className="opciones">
        <legend>Tipo de venta</legend>
        {(Object.keys(TIPOS_VENTA) as TipoVenta[]).map((valor) => (
          <label key={valor} className="opcion-radio">
            <input
              type="radio"
              name="tipo"
              value={valor}
              checked={tipo === valor}
              onChange={() => setTipo(valor)}
            />
            {TIPOS_VENTA[valor]}
          </label>
        ))}
      </fieldset>

      <div className="rejilla-2">
        <label className="campo">
          <span>Cantidad</span>
          <input type="number" min={1} step={1} value={cantidad} onChange={(e) => setCantidad(e.target.value)} />
        </label>
        <label className="campo">
          <span>Precio por unidad</span>
          <input type="number" min={1} step={1} inputMode="numeric" value={precio} onChange={(e) => setPrecio(e.target.value)} />
        </label>
      </div>

      {tipo === "orden" && (
        <label className="campo">
          <span>Tarifa por reajustes (si cambiaste el precio de la orden)</span>
          <input type="number" min={0} step={1} inputMode="numeric" value={tarifaExtra} onChange={(e) => setTarifaExtra(e.target.value)} />
          <span className="campo__ayuda">Cada reajuste vuelve a cobrar la tarifa y el juego no la devuelve.</span>
        </label>
      )}

      <label className="campo">
        <span>Fecha y hora (opcional)</span>
        <input type="datetime-local" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        <span className="campo__ayuda">Si la dejas vacía se usa el momento actual.</span>
      </label>

      <div role="group" aria-label="Vista previa del desglose" className="vista-previa">
        <dl>
          <div><dt>Bruto</dt><dd className="num">{desglose ? plataCompleta(desglose.bruto) : "—"}</dd></div>
          <div><dt>Impuesto de venta (4 %)</dt><dd className="num">{desglose ? plataCompleta(desglose.impuesto) : "—"}</dd></div>
          {tipo === "orden" && (
            <div><dt>Tarifa de publicación (2.5 %)</dt><dd className="num">{desglose ? plataCompleta(desglose.tarifa) : "—"}</dd></div>
          )}
          <div className="vista-previa__neto"><dt>Neto</dt><dd className="num">{desglose ? plataCompleta(desglose.neto) : "—"}</dd></div>
        </dl>
        <p className="campo__ayuda">Estimación con premium activo; el cálculo definitivo lo hace el servidor.</p>
      </div>

      {registrar.isError && <p role="alert" className="caja caja--error">{registrar.error.message}</p>}

      <div>
        <button type="submit" className="boton boton--primario boton--grande" disabled={!valido || registrar.isPending}>
          {registrar.isPending ? "Guardando…" : "Guardar venta"}
        </button>
      </div>
    </form>
  );
}
