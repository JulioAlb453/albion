import { useEvolucion, useReportes, useSaldoInicial } from "../../api/consultas";
import { CATEGORIAS_GASTO } from "../../api/tipos";
import { useSesion } from "../../sesion/ContextoSesion";
import { Bloque, Plata, Vacio } from "../../ui/Bloque";
import { diaCorto, plataCompleta, plataCorta, signo } from "../../util/formato";
import { CargaFallida } from "../CargaFallida";
import { FormularioSaldoInicial } from "../FormularioSaldoInicial";
import { GraficaBalance, GraficaDona } from "../Graficas";

export function BloqueSaldo({ dias }: { dias: number | null }) {
  const saldo = useSaldoInicial();
  const evolucion = useEvolucion();
  const { usuario } = useSesion();
  const marco = { titulo: "Saldo del gremio", columnas: 8 as const, filas: 2 as const, acento: true };

  const fallo = saldo.error ?? evolucion.error;
  if (fallo) {
    return (
      <Bloque {...marco}>
        <CargaFallida que="el saldo" error={fallo} alReintentar={() => { void saldo.refetch(); void evolucion.refetch(); }} />
      </Bloque>
    );
  }
  if (!saldo.isSuccess || !evolucion.isSuccess) {
    return <Bloque {...marco}><p className="texto-2" role="status">Cargando…</p></Bloque>;
  }
  if (saldo.data === null) {
    return (
      <Bloque {...marco}>
        {usuario.puede_registrar ? (
          <FormularioSaldoInicial />
        ) : (
          <Vacio titulo="Todavía no se configuró el saldo inicial">Pídele a un administrador que lo configure.</Vacio>
        )}
      </Bloque>
    );
  }

  const puntos = evolucion.data;
  const actual = puntos.at(-1)?.saldo ?? saldo.data.monto;
  const variacion = actual - saldo.data.monto;
  return (
    <Bloque {...marco}>
      <div>
        <Plata valor={actual} />
        <p className="texto-2">
          <span className={variacion >= 0 ? "positivo" : "negativo"}>{signo(variacion)}</span> desde el saldo inicial
          ({plataCorta(saldo.data.monto)} el {diaCorto(saldo.data.fecha)})
        </p>
      </div>
      <GraficaBalance puntos={dias ? puntos.slice(-dias) : puntos} llena />
    </Bloque>
  );
}

export function BloqueResumen({ desde }: { desde?: string }) {
  const reportes = useReportes({ desde });
  return (
    <Bloque titulo="Resumen del periodo" columnas={4}>
      {reportes.isError ? (
        <CargaFallida que="el resumen" error={reportes.error} alReintentar={() => void reportes.refetch()} />
      ) : !reportes.isSuccess ? (
        <p className="texto-2" role="status">Cargando…</p>
      ) : (
        <div className="estadisticas">
          <div className="estadistica">
            <span className="estadistica__etiqueta">Ventas netas</span>
            <Plata valor={reportes.data.ventas_netas} tamano="media" />
          </div>
          <div className="estadistica">
            <span className="estadistica__etiqueta">Gastos</span>
            <Plata valor={reportes.data.gastos_totales} tamano="media" />
          </div>
          <div className="estadistica">
            <span className="estadistica__etiqueta">Resultado</span>
            <Plata valor={reportes.data.resultado} tamano="media" conTono />
          </div>
          <div className="estadistica">
            <span className="estadistica__etiqueta">Impuestos pagados</span>
            <Plata valor={reportes.data.impuestos.total} tamano="media" />
          </div>
        </div>
      )}
    </Bloque>
  );
}

export function BloqueImpuestosGastos({ desde }: { desde?: string }) {
  const reportes = useReportes({ desde });
  return (
    <Bloque titulo="Impuestos y gastos" columnas={4}>
      {reportes.isError ? (
        <CargaFallida que="los impuestos y gastos" error={reportes.error} alReintentar={() => void reportes.refetch()} />
      ) : !reportes.isSuccess ? (
        <p className="texto-2" role="status">Cargando…</p>
      ) : (
        <>
          <GraficaDona
            datos={reportes.data.gastos_por_categoria.map((g) => ({ nombre: CATEGORIAS_GASTO[g.categoria], valor: g.monto }))}
          />
          <ul className="lista">
            <li className="lista__fila">
              <span className="lista__principal">Impuesto de venta</span>
              <span className="num" title={plataCompleta(reportes.data.impuestos.impuesto_venta)}>
                {plataCorta(reportes.data.impuestos.impuesto_venta)}
              </span>
            </li>
            <li className="lista__fila">
              <span className="lista__principal">Tarifa de publicación</span>
              <span className="num" title={plataCompleta(reportes.data.impuestos.tarifa_publicacion)}>
                {plataCorta(reportes.data.impuestos.tarifa_publicacion)}
              </span>
            </li>
          </ul>
        </>
      )}
    </Bloque>
  );
}
