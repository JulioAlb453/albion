import { useState, type FormEvent } from "react";
import { useCorregirVenta, useObjeto } from "../api/consultas";
import type { Venta } from "../api/tipos";
import { useAvisos } from "../ui/Avisos";
import { ImagenObjeto } from "../ui/ImagenObjeto";
import { admiteOpciones, ajustar, CamposObjeto } from "./CamposObjeto";

interface Props {
  venta: Venta;
  alTerminar: () => void;
}

/** Corrige el encantamiento y la calidad de una venta registrada. Precio e impuestos no cambian. */
export function FormularioCorregirVenta({ venta, alTerminar }: Props) {
  const objeto = useObjeto(venta.objeto.base_id);
  const [encantamiento, setEncantamiento] = useState(venta.objeto.encantamiento);
  const [calidad, setCalidad] = useState(venta.objeto.calidad);
  const corregir = useCorregirVenta();
  const { avisar } = useAvisos();

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    if (!objeto.data) return;
    corregir.mutate(
      { id: venta.id, ...ajustar(objeto.data, encantamiento, calidad) },
      {
        onSuccess: () => {
          avisar("Venta corregida", "exito");
          alTerminar();
        },
        onError: (error) => avisar(error.message, "error"),
      },
    );
  };

  return (
    <form className="formulario" onSubmit={enviar}>
      <div className="selector selector--elegido">
        <ImagenObjeto baseId={venta.objeto.base_id} encantamiento={encantamiento} calidad={calidad} tamano={64} />
        <div className="lista__principal">
          <div className="lista__titulo">{venta.objeto.nombre ?? venta.objeto.base_id}</div>
          <div className="lista__detalle">{venta.cantidad} × {venta.ciudad}</div>
        </div>
      </div>

      {objeto.isPending && <p className="texto-2" role="status">Cargando el objeto…</p>}
      {objeto.isError && <p role="alert" className="caja caja--error">No se encontró el objeto en el catálogo.</p>}
      {objeto.data && !admiteOpciones(objeto.data) && (
        <p className="texto-2">Este objeto no tiene encantamiento ni calidad que corregir.</p>
      )}
      {objeto.data && admiteOpciones(objeto.data) && (
        <div className="rejilla-2">
          <CamposObjeto
            objeto={objeto.data} encantamiento={encantamiento} calidad={calidad}
            alCambiarEncantamiento={setEncantamiento} alCambiarCalidad={setCalidad}
          />
        </div>
      )}
      <p className="campo__ayuda">El precio, la cantidad y los impuestos se quedan como estaban.</p>

      <div>
        <button
          type="submit"
          className="boton boton--primario boton--grande"
          disabled={!objeto.data || !admiteOpciones(objeto.data) || corregir.isPending}
        >
          {corregir.isPending ? "Guardando…" : "Guardar"}
        </button>
      </div>
    </form>
  );
}
