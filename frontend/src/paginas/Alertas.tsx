import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAlertas, useEliminarSeguimiento, useObjeto, useSeguimientos } from "../api/consultas";
import { TIPOS_VENTA } from "../api/tipos";
import { CargaFallida } from "../componentes/CargaFallida";
import { FormularioSeguimiento } from "../componentes/FormularioSeguimiento";
import { useSesion } from "../sesion/ContextoSesion";
import { useAvisos } from "../ui/Avisos";
import { Bloque, Insignia, Plata, Vacio } from "../ui/Bloque";
import { Cajon } from "../ui/Cajon";
import { Icono } from "../ui/Icono";
import { antiguedad, etiquetaCalidad, fechaHora, plataCorta } from "../util/formato";

function entero(texto: string | null, defecto: number, minimo: number, maximo: number): number {
  const n = Number(texto);
  return texto !== null && Number.isInteger(n) && n >= minimo && n <= maximo ? n : defecto;
}

export function Alertas() {
  const { usuario } = useSesion();
  const { avisar } = useAvisos();
  const [params, setParams] = useSearchParams();
  const baseIdDelEnlace = params.get("base_id");
  const objetoDelEnlace = useObjeto(usuario.puede_registrar ? baseIdDelEnlace : null);
  const [abierto, setAbierto] = useState(false);
  const [confirmando, setConfirmando] = useState<number | null>(null);
  const seguimientos = useSeguimientos();
  const alertas = useAlertas(50);
  const eliminar = useEliminarSeguimiento();

  // Viniendo del botón "Vigilar" del comparador, el formulario se abre solo con el objeto elegido.
  useEffect(() => {
    if (objetoDelEnlace.data) setAbierto(true);
  }, [objetoDelEnlace.data]);

  useEffect(() => {
    if (confirmando === null) return;
    const temporizador = setTimeout(() => setConfirmando(null), 4_000);
    return () => clearTimeout(temporizador);
  }, [confirmando]);

  const cerrar = () => {
    setAbierto(false);
    if (baseIdDelEnlace) setParams({}, { replace: true }); // para que no se reabra al recargar
  };

  const dejarDeVigilar = (id: number) => {
    if (confirmando !== id) {
      setConfirmando(id);
      return;
    }
    eliminar.mutate(id, {
      onSuccess: () => avisar("Dejaste de vigilar el objeto", "exito"),
      onError: (error) => avisar(error.message, "error"),
    });
    setConfirmando(null);
  };

  return (
    <div className="bento">
      <Bloque
        titulo="Objetos vigilados"
        columnas={6}
        accion={
          usuario.puede_registrar ? (
            <button type="button" className="boton boton--primario" onClick={() => setAbierto(true)}>
              <Icono nombre="vigilar" tamano={18} /> Vigilar un objeto
            </button>
          ) : undefined
        }
      >
        {seguimientos.isError ? (
          <CargaFallida que="los objetos vigilados" error={seguimientos.error} alReintentar={() => void seguimientos.refetch()} />
        ) : !seguimientos.isSuccess ? (
          <p className="texto-2" role="status">Cargando…</p>
        ) : seguimientos.data.length === 0 ? (
          <Vacio titulo="Todavía no vigilas ningún objeto">
            Elige los objetos que más vendes y la app te avisará cuando convenga venderlos en otra ciudad.
          </Vacio>
        ) : (
          <ul className="lista">
            {seguimientos.data.map((s) => {
              const nombre = s.objeto.nombre ?? s.objeto.base_id;
              return (
                <li key={s.id} className="lista__fila">
                  <div className="lista__principal">
                    <div className="lista__titulo">{nombre}</div>
                    <div className="lista__detalle">{s.objeto.etiqueta} · {etiquetaCalidad(s.objeto.calidad)}</div>
                  </div>
                  <div className="derecha lista__detalle">
                    {s.porcentaje_minimo !== null && <div>+{s.porcentaje_minimo} % sobre {s.ciudad_referencia}</div>}
                    {s.neto_minimo !== null && <div>neto por unidad ≥ {plataCorta(s.neto_minimo)}</div>}
                  </div>
                  {usuario.puede_registrar && (
                    <button
                      type="button"
                      className={`boton boton--chico ${confirmando === s.id ? "boton--peligro" : "boton--fantasma"}`}
                      aria-label={confirmando === s.id ? "Confirmar" : `Dejar de vigilar ${nombre}`}
                      onClick={() => dejarDeVigilar(s.id)}
                    >
                      {confirmando === s.id ? "¿Seguro?" : <Icono nombre="borrar" tamano={16} />}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </Bloque>

      <Bloque titulo="Alertas recientes" columnas={6}>
        {alertas.isError ? (
          <CargaFallida que="las alertas" error={alertas.error} alReintentar={() => void alertas.refetch()} />
        ) : !alertas.isSuccess ? (
          <p className="texto-2" role="status">Cargando…</p>
        ) : alertas.data.length === 0 ? (
          <Vacio titulo="Sin alertas todavía">
            Los precios de tus objetos vigilados se revisan cada pocos minutos mientras la PC del gremio esté encendida.
          </Vacio>
        ) : (
          <ul className="lista">
            {alertas.data.map((alerta) => (
              <li key={alerta.id} className="lista__fila">
                <div className="lista__principal">
                  <div className="lista__titulo">{alerta.objeto.nombre ?? alerta.objeto.base_id}</div>
                  <div className="lista__detalle">{alerta.motivo}</div>
                  <div className="fila fila--junta">
                    <Insignia tono="acento">{alerta.ciudad}</Insignia>
                    <Insignia>{TIPOS_VENTA[alerta.tipo]}</Insignia>
                    <span className="lista__detalle" title={fechaHora(alerta.fecha)}>
                      {antiguedad((Date.now() - new Date(alerta.fecha).getTime()) / 1000)}
                    </span>
                  </div>
                </div>
                <Plata valor={alerta.neto_unitario} tamano="chica" />
              </li>
            ))}
          </ul>
        )}
      </Bloque>

      <Cajon abierto={abierto} titulo="Vigilar un objeto" alCerrar={cerrar}>
        <FormularioSeguimiento
          key={objetoDelEnlace.data?.base_id ?? "nuevo"}
          prefill={
            objetoDelEnlace.data
              ? { objeto: objetoDelEnlace.data, encantamiento: entero(params.get("enc"), 0, 0, 4), calidad: entero(params.get("cal"), 1, 1, 5) }
              : undefined
          }
          alTerminar={cerrar}
        />
      </Cajon>
    </div>
  );
}
