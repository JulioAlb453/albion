import { useMemo, useState } from "react";
import { useDescargar, useReportes } from "../api/consultas";
import { CATEGORIAS_GASTO } from "../api/tipos";
import { CargaFallida } from "../componentes/CargaFallida";
import { GraficaBarras, GraficaDona } from "../componentes/Graficas";
import { Bloque, Plata, Vacio } from "../ui/Bloque";
import { Icono } from "../ui/Icono";
import { diaLocalHaceDias, etiquetaCalidad, finDelDia, inicioDelDia, plataCompleta, plataCorta } from "../util/formato";

const ATAJOS = [
  { texto: "7 días", dias: 7 },
  { texto: "30 días", dias: 30 },
  { texto: "90 días", dias: 90 },
  { texto: "Todo", dias: null },
] as const;

export function Reportes() {
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const periodo = useMemo(
    () => ({ desde: desde ? inicioDelDia(desde) : undefined, hasta: hasta ? finDelDia(hasta) : undefined }),
    [desde, hasta],
  );
  const reportes = useReportes(periodo);
  const descargar = useDescargar();

  const activo = (dias: number | null) =>
    dias === null ? !desde && !hasta : desde === diaLocalHaceDias(dias) && hasta === "";
  const elegirAtajo = (dias: number | null) => {
    setDesde(dias === null ? "" : diaLocalHaceDias(dias));
    setHasta("");
  };

  const datos = reportes.data;
  const bruto = datos?.ganancia_por_objeto.reduce((suma, g) => suma + g.bruto, 0) ?? 0;
  const parteEnImpuestos = datos && bruto > 0 ? (datos.impuestos.total / bruto) * 100 : 0;

  return (
    <div className="pila pila--grande">
      <Bloque
        titulo="Periodo"
        columnas={12}
        accion={
          <div className="acciones-fila">
            <button
              type="button" className="boton" title="El CSV lleva solo la ganancia por objeto"
              onClick={() => void descargar("/api/reportes/exportar", { ...periodo, formato: "csv" })}
            >
              <Icono nombre="descargar" tamano={18} /> Exportar CSV
            </button>
            <button type="button" className="boton" onClick={() => void descargar("/api/reportes/exportar", { ...periodo, formato: "xlsx" })}>
              <Icono nombre="descargar" tamano={18} /> Exportar Excel
            </button>
          </div>
        }
      >
        <div className="herramientas">
          <div className="chips" role="group" aria-label="Atajos de periodo">
            {ATAJOS.map(({ texto, dias }) => (
              <button key={texto} type="button" className="chip" aria-pressed={activo(dias)} onClick={() => elegirAtajo(dias)}>
                {texto}
              </button>
            ))}
          </div>
          <label className="campo">
            <span>Desde</span>
            <input type="date" value={desde} max={hasta || undefined} onChange={(e) => setDesde(e.target.value)} />
          </label>
          <label className="campo">
            <span>Hasta</span>
            <input type="date" value={hasta} min={desde || undefined} onChange={(e) => setHasta(e.target.value)} />
          </label>
        </div>
      </Bloque>

      {reportes.isError && <CargaFallida que="el reporte" error={reportes.error} alReintentar={() => void reportes.refetch()} />}
      {reportes.isPending && <p className="texto-2" role="status">Cargando…</p>}

      {datos && (
        <div className="bento">
          <Bloque titulo="Resultado del periodo" columnas={4} acento>
            <Plata valor={datos.resultado} conTono />
            <p className="texto-2">
              {plataCorta(datos.ventas_netas)} de ventas netas − {plataCorta(datos.gastos_totales)} de gastos
            </p>
            {datos.ingresos_extra > 0 && <p className="texto-2">+ {plataCorta(datos.ingresos_extra)} de otros ingresos</p>}
            {datos.pagos_semanales > 0 && <p className="texto-2">− {plataCorta(datos.pagos_semanales)} de pagos semanales</p>}
          </Bloque>

          <Bloque titulo="Impuestos pagados" columnas={4}>
            <Plata valor={datos.impuestos.total} />
            <p className="texto-2">
              {bruto > 0 ? `${parteEnImpuestos.toFixed(1)} % de lo vendido se fue en impuestos y tarifas` : "Todavía no hay ventas que gravar"}
            </p>
            <ul className="lista">
              <li className="lista__fila">
                <span className="lista__principal">Impuesto de venta</span>
                <span className="num" title={plataCompleta(datos.impuestos.impuesto_venta)}>{plataCorta(datos.impuestos.impuesto_venta)}</span>
              </li>
              <li className="lista__fila">
                <span className="lista__principal">Tarifa de publicación</span>
                <span className="num" title={plataCompleta(datos.impuestos.tarifa_publicacion)}>{plataCorta(datos.impuestos.tarifa_publicacion)}</span>
              </li>
            </ul>
          </Bloque>

          <Bloque titulo="Gastos por categoría" columnas={4}>
            <GraficaDona datos={datos.gastos_por_categoria.map((g) => ({ nombre: CATEGORIAS_GASTO[g.categoria], valor: g.monto }))} />
          </Bloque>

          <Bloque titulo="Ganancia por objeto" columnas={12}>
            {datos.ganancia_por_objeto.length === 0 ? (
              <Vacio titulo="Sin ventas en este periodo" />
            ) : (
              <>
                <GraficaBarras
                  datos={datos.ganancia_por_objeto.slice(0, 8).map((g) => ({
                    nombre: `${g.objeto.nombre ?? g.objeto.base_id} ${g.objeto.etiqueta}`,
                    valor: g.neto,
                  }))}
                />
                <div className="tabla-envoltorio">
                  <table className="tabla">
                    <thead>
                      <tr>
                        <th>Objeto</th><th className="num">Unidades</th><th className="num">Bruto</th>
                        <th className="num">Impuesto</th><th className="num">Tarifa</th><th className="num">Neto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {datos.ganancia_por_objeto.map((g) => (
                        <tr key={`${g.objeto.base_id}-${g.objeto.encantamiento}-${g.objeto.calidad}`}>
                          <td>
                            <div className="tabla__objeto">
                              <span>{g.objeto.nombre ?? g.objeto.base_id}</span>
                              <span className="lista__detalle">{g.objeto.etiqueta} · {etiquetaCalidad(g.objeto.calidad)}</span>
                            </div>
                          </td>
                          <td className="num">{g.unidades}</td>
                          <td className="num">{plataCompleta(g.bruto)}</td>
                          <td className="num">{plataCompleta(g.impuesto)}</td>
                          <td className="num">{plataCompleta(g.tarifa_publicacion)}</td>
                          <td className="num"><Plata valor={g.neto} tamano="chica" /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="nota">Es el neto de las ventas de cada objeto: el gremio no registra cuánto costó comprarlo, así que no resta costos.</p>
              </>
            )}
          </Bloque>
        </div>
      )}
    </div>
  );
}
