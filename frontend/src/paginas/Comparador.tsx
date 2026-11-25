import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useComparacion, useObjeto } from "../api/consultas";
import { etiquetaCalidad } from "../util/formato";
import type { Ciudad, TipoVenta } from "../api/tipos";
import { useRegistro } from "../componentes/ContextoRegistro";
import { SelectorObjeto } from "../componentes/SelectorObjeto";
import { TarjetaCiudad } from "../componentes/TarjetaCiudad";
import { useSesion } from "../sesion/ContextoSesion";
import { Bloque, Vacio } from "../ui/Bloque";
import { Icono } from "../ui/Icono";
import { mejorCiudad } from "../util/comparacion";

/** Lee un número entero de la dirección, o el valor por defecto si falta o no es válido. */
function entero(texto: string | null, defecto: number, minimo: number, maximo: number): number {
  const numero = Number(texto);
  return texto !== null && Number.isInteger(numero) && numero >= minimo && numero <= maximo ? numero : defecto;
}

export function Comparador() {
  const [params, setParams] = useSearchParams();
  const { usuario } = useSesion();
  const { abrirVenta } = useRegistro();

  const baseId = params.get("base_id");
  const encantamiento = entero(params.get("enc"), 0, 0, 4);
  const calidad = entero(params.get("cal"), 1, 1, 5);
  const cantidad = entero(params.get("cant"), 1, 1, 100_000);
  const [textoCantidad, setTextoCantidad] = useState(String(cantidad));

  const objeto = useObjeto(baseId);
  const consulta =
    baseId && objeto.data
      ? {
          base_id: baseId,
          encantamiento: objeto.data.tiene_calidad ? encantamiento : 0,
          calidad: objeto.data.tiene_calidad ? calidad : 1,
          cantidad,
        }
      : null;
  const comparacion = useComparacion(consulta);

  const cambiar = (cambios: Record<string, string | null>) =>
    setParams(
      (actuales) => {
        const nuevos = new URLSearchParams(actuales);
        for (const [clave, valor] of Object.entries(cambios)) {
          if (valor === null) nuevos.delete(clave);
          else nuevos.set(clave, valor);
        }
        return nuevos;
      },
      { replace: true },
    );

  const ciudades = comparacion.data ?? [];
  const coronada = mejorCiudad(ciudades);
  const ciudadMejor = coronada?.confiable ? coronada.ciudad : null;

  const registrar = (ciudad: Ciudad, tipo: TipoVenta, precio: number) => {
    if (!objeto.data || !consulta) return;
    abrirVenta({
      objeto: objeto.data,
      encantamiento: consulta.encantamiento,
      calidad: consulta.calidad,
      cantidad: consulta.cantidad,
      ciudad,
      tipo,
      precio_unitario: precio,
    });
  };

  return (
    <div className="pila pila--grande">
      <Bloque
        titulo="Objeto a vender"
        accion={
          usuario.puede_registrar && objeto.data ? (
            <Link
              className="boton boton--fantasma"
              to={`/alertas?base_id=${objeto.data.base_id}&enc=${consulta?.encantamiento ?? 0}&cal=${consulta?.calidad ?? 1}`}
            >
              <Icono nombre="vigilar" tamano={18} /> Vigilar
            </Link>
          ) : undefined
        }
      >
        <SelectorObjeto
          valor={objeto.data ?? null}
          alElegir={(elegido) =>
            elegido
              ? cambiar({ base_id: elegido.base_id, enc: null, cal: null })
              : cambiar({ base_id: null, enc: null, cal: null })
          }
        />
        {baseId && objeto.isError && (
          <p role="alert" className="caja caja--error">No se encontró ese objeto en el catálogo.</p>
        )}
        {objeto.data && (
          <div className="controles">
            {objeto.data.tiene_calidad && (
              <>
                <label className="campo">
                  <span>Encantamiento</span>
                  <select value={encantamiento} onChange={(e) => cambiar({ enc: e.target.value })}>
                    {[0, 1, 2, 3, 4].map((n) => (
                      <option key={n} value={n}>{n === 0 ? ".0 (sin encantar)" : `.${n}`}</option>
                    ))}
                  </select>
                </label>
                <label className="campo">
                  <span>Calidad</span>
                  <select value={calidad} onChange={(e) => cambiar({ cal: e.target.value })}>
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>{etiquetaCalidad(n)}</option>
                    ))}
                  </select>
                </label>
              </>
            )}
            <label className="campo">
              <span>Cantidad</span>
              <input
                type="number"
                min={1}
                value={textoCantidad}
                onChange={(e) => {
                  setTextoCantidad(e.target.value);
                  const n = Number(e.target.value);
                  if (Number.isInteger(n) && n >= 1) cambiar({ cant: String(n) });
                }}
              />
            </label>
          </div>
        )}
      </Bloque>

      {!baseId && (
        <Vacio titulo="Elige un objeto para comparar">
          Verás en qué ciudad conviene venderlo y si rinde más como venta directa o como orden de venta.
        </Vacio>
      )}

      {consulta && comparacion.isPending && <p className="texto-2" role="status">Consultando precios…</p>}
      {comparacion.isError && (
        <div className="caja caja--error pila" role="alert">
          <p>{comparacion.error.message}</p>
          <div><button className="boton" onClick={() => void comparacion.refetch()}>Reintentar</button></div>
        </div>
      )}
      {comparacion.isSuccess && ciudades.length === 0 && (
        <Vacio titulo="Todavía nadie ha reportado precios de este objeto">
          Los precios los suben los jugadores. Prueba con otra calidad o encantamiento.
        </Vacio>
      )}
      {ciudades.length > 0 && (
        <div className="ciudades">
          {ciudades.map((ciudad) => (
            <TarjetaCiudad
              key={ciudad.ciudad}
              comparacion={ciudad}
              esMejor={ciudad.ciudad === ciudadMejor}
              puedeRegistrar={usuario.puede_registrar}
              cantidad={cantidad}
              alRegistrar={registrar}
            />
          ))}
        </div>
      )}
    </div>
  );
}
