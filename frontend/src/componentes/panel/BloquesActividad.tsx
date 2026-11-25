import { useQueries } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useCliente } from "../../api/ContextoApi";
import { opcionesComparacion, useAlertas, useSeguimientos, useVentas } from "../../api/consultas";
import { TIPOS_VENTA, type Seguimiento } from "../../api/tipos";
import { Bloque, Insignia, Plata, Vacio } from "../../ui/Bloque";
import { mejorCiudad, opcionGanadora, ventajaSobre } from "../../util/comparacion";
import { antiguedad, etiquetaCalidad, fechaHora } from "../../util/formato";
import { CargaFallida } from "../CargaFallida";

function FilaOportunidad({ seguimiento, consulta }: { seguimiento: Seguimiento; consulta: { data?: Parameters<typeof mejorCiudad>[0]; isPending: boolean; isError: boolean } }) {
  const { objeto, ciudad_referencia: referencia } = seguimiento;
  const ciudades = consulta.data ?? [];
  const mejor = mejorCiudad(ciudades);
  const opcion = mejor ? opcionGanadora(mejor) : null;
  const ventaja = ventajaSobre(ciudades, referencia);

  return (
    <li className="lista__fila">
      <div className="lista__principal">
        <div className="lista__titulo">{objeto.nombre ?? objeto.base_id}</div>
        <div className="lista__detalle">{objeto.etiqueta} · {etiquetaCalidad(objeto.calidad)}</div>
      </div>
      {consulta.isPending && <span className="texto-3">Consultando…</span>}
      {consulta.isError && <span className="texto-3">Sin respuesta de la API</span>}
      {mejor && opcion && (
        <>
          <div className="derecha">
            <div className="lista__titulo">{mejor.ciudad}</div>
            <div className="lista__detalle">
              {TIPOS_VENTA[opcion.tipo]} {!mejor.confiable && <Insignia tono="aviso">Dato viejo</Insignia>}
            </div>
          </div>
          <div className="derecha">
            <Plata valor={opcion.neto_unitario} tamano="chica" />
            <div className="lista__detalle positivo">
              {ventaja !== null && ventaja > 0 ? `+${Math.round(ventaja)} % sobre ${referencia}` : " "}
            </div>
          </div>
        </>
      )}
      {consulta.data && !mejor && <span className="texto-3">Sin datos de precios</span>}
    </li>
  );
}

export function BloqueOportunidades() {
  const cliente = useCliente();
  const seguimientos = useSeguimientos();
  const vigilados = (seguimientos.data ?? []).slice(0, 4);
  const consultas = useQueries({
    queries: vigilados.map((s) =>
      opcionesComparacion(cliente, {
        base_id: s.objeto.base_id, encantamiento: s.objeto.encantamiento, calidad: s.objeto.calidad, cantidad: 1,
      }),
    ),
  });

  return (
    <Bloque titulo="Mejores oportunidades" columnas={6} accion={<Link className="boton boton--fantasma" to="/comparador">Comparar</Link>}>
      {seguimientos.isError ? (
        <CargaFallida que="los objetos vigilados" error={seguimientos.error} alReintentar={() => void seguimientos.refetch()} />
      ) : !seguimientos.isSuccess ? (
        <p className="texto-2" role="status">Cargando…</p>
      ) : vigilados.length === 0 ? (
        <Vacio titulo="Todavía no vigilas ningún objeto" accion={<Link className="boton" to="/alertas">Vigilar un objeto</Link>}>
          Aquí verás dónde conviene vender cada uno de los objetos que vigiles, y cuánto más que en tu ciudad principal.
        </Vacio>
      ) : (
        <ul className="lista">
          {vigilados.map((seguimiento, indice) => (
            <FilaOportunidad key={seguimiento.id} seguimiento={seguimiento} consulta={consultas[indice]!} />
          ))}
        </ul>
      )}
    </Bloque>
  );
}

export function BloqueAlertas() {
  const alertas = useAlertas(5);
  return (
    <Bloque titulo="Alertas recientes" columnas={6} accion={<Link className="boton boton--fantasma" to="/alertas">Ver todas</Link>}>
      {alertas.isError ? (
        <CargaFallida que="las alertas" error={alertas.error} alReintentar={() => void alertas.refetch()} />
      ) : !alertas.isSuccess ? (
        <p className="texto-2" role="status">Cargando…</p>
      ) : alertas.data.length === 0 ? (
        <Vacio titulo="Sin alertas todavía">Se revisan los precios de tus objetos vigilados cada pocos minutos.</Vacio>
      ) : (
        <ul className="lista">
          {alertas.data.map((alerta) => (
            <li key={alerta.id} className="lista__fila">
              <div className="lista__principal">
                <div className="lista__titulo">{alerta.objeto.nombre ?? alerta.objeto.base_id} <span className="texto-3">{alerta.objeto.etiqueta}</span></div>
                <div className="lista__detalle">{alerta.motivo}</div>
              </div>
              <span className="texto-3" title={fechaHora(alerta.fecha)}>
                {antiguedad((Date.now() - new Date(alerta.fecha).getTime()) / 1000)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Bloque>
  );
}

export function BloqueUltimasVentas() {
  const ventas = useVentas();
  const recientes = [...(ventas.data ?? [])].sort((a, b) => b.fecha.localeCompare(a.fecha)).slice(0, 6);
  return (
    <Bloque titulo="Últimas ventas" columnas={12} accion={<Link className="boton boton--fantasma" to="/ventas">Ver todas</Link>}>
      {ventas.isError ? (
        <CargaFallida que="las ventas" error={ventas.error} alReintentar={() => void ventas.refetch()} />
      ) : !ventas.isSuccess ? (
        <p className="texto-2" role="status">Cargando…</p>
      ) : recientes.length === 0 ? (
        <Vacio titulo="Todavía no hay ventas registradas">Cuando registres la primera, aparecerá aquí.</Vacio>
      ) : (
        <div className="tabla-envoltorio">
          <table className="tabla">
            <thead>
              <tr>
                <th>Fecha</th><th>Objeto</th><th>Ciudad</th><th>Tipo</th><th className="num">Neto</th>
              </tr>
            </thead>
            <tbody>
              {recientes.map((venta) => (
                <tr key={venta.id}>
                  <td className="texto-2">{fechaHora(venta.fecha)}</td>
                  <td>
                    <div className="tabla__objeto">
                      <span>{venta.objeto.nombre ?? venta.objeto.base_id}</span>
                      <span className="lista__detalle">{venta.objeto.etiqueta} · {etiquetaCalidad(venta.objeto.calidad)} · ×{venta.cantidad}</span>
                    </div>
                  </td>
                  <td>{venta.ciudad}</td>
                  <td>{TIPOS_VENTA[venta.tipo]}</td>
                  <td className="num"><Plata valor={venta.neto} tamano="chica" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Bloque>
  );
}
