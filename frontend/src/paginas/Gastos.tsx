import { useEffect, useMemo, useState } from "react";
import { useDescargar, useEliminarGasto, useGastos, useImportarGastos } from "../api/consultas";
import { CATEGORIAS_GASTO, type CategoriaGasto } from "../api/tipos";
import { CargaFallida } from "../componentes/CargaFallida";
import { DialogoImportar } from "../componentes/DialogoImportar";
import { FormularioGasto } from "../componentes/FormularioGasto";
import { useSesion } from "../sesion/ContextoSesion";
import { useAvisos } from "../ui/Avisos";
import { Bloque, Insignia, Plata, Vacio } from "../ui/Bloque";
import { Cajon } from "../ui/Cajon";
import { Icono } from "../ui/Icono";
import { fechaHora, finDelDia, inicioDelDia } from "../util/formato";

export function Gastos() {
  const { usuario } = useSesion();
  const { avisar } = useAvisos();
  const [categoria, setCategoria] = useState<CategoriaGasto | "">("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [registrando, setRegistrando] = useState(false);
  const [importando, setImportando] = useState(false);
  const [confirmando, setConfirmando] = useState<number | null>(null);

  const filtro = useMemo(
    () => ({ desde: desde ? inicioDelDia(desde) : undefined, hasta: hasta ? finDelDia(hasta) : undefined, categoria }),
    [desde, hasta, categoria],
  );
  const gastos = useGastos(filtro);
  const eliminar = useEliminarGasto();
  const importar = useImportarGastos();
  const descargar = useDescargar();

  useEffect(() => {
    if (confirmando === null) return;
    const temporizador = setTimeout(() => setConfirmando(null), 4_000);
    return () => clearTimeout(temporizador);
  }, [confirmando]);

  // La API los manda del más viejo al más nuevo; en un registro lo reciente va arriba.
  const filas = useMemo(() => [...(gastos.data ?? [])].sort((a, b) => b.fecha.localeCompare(a.fecha)), [gastos.data]);
  const hayFiltros = Boolean(desde || hasta || categoria);
  const total = filas.reduce((suma, g) => suma + g.monto, 0);

  const borrar = (id: number) => {
    if (confirmando !== id) {
      setConfirmando(id);
      return;
    }
    eliminar.mutate(id, {
      onSuccess: () => avisar("Gasto eliminado", "exito"),
      onError: (error) => avisar(error.message, "error"),
    });
    setConfirmando(null);
  };

  return (
    <div className="pila pila--grande">
      <Bloque
        titulo="Gastos registrados"
        columnas={12}
        accion={
          <div className="acciones-fila">
            <button type="button" className="boton" onClick={() => void descargar("/api/gastos/exportar", { ...filtro, formato: "csv" })}>
              <Icono nombre="descargar" tamano={18} /> Exportar CSV
            </button>
            <button type="button" className="boton" onClick={() => void descargar("/api/gastos/exportar", { ...filtro, formato: "xlsx" })}>
              <Icono nombre="descargar" tamano={18} /> Exportar Excel
            </button>
            {usuario.puede_registrar && (
              <>
                <button type="button" className="boton" onClick={() => setImportando(true)}>
                  <Icono nombre="subir" tamano={18} /> Importar
                </button>
                <button type="button" className="boton boton--primario" onClick={() => setRegistrando(true)}>
                  <Icono nombre="mas" tamano={18} /> Registrar gasto
                </button>
              </>
            )}
          </div>
        }
      >
        <div className="herramientas">
          <label className="campo">
            <span>Categoría</span>
            <select value={categoria} onChange={(e) => setCategoria(e.target.value as CategoriaGasto | "")}>
              <option value="">Todas</option>
              {(Object.keys(CATEGORIAS_GASTO) as CategoriaGasto[]).map((c) => <option key={c} value={c}>{CATEGORIAS_GASTO[c]}</option>)}
            </select>
          </label>
          <label className="campo">
            <span>Desde</span>
            <input type="date" value={desde} max={hasta || undefined} onChange={(e) => setDesde(e.target.value)} />
          </label>
          <label className="campo">
            <span>Hasta</span>
            <input type="date" value={hasta} min={desde || undefined} onChange={(e) => setHasta(e.target.value)} />
          </label>
          {hayFiltros && (
            <button type="button" className="boton boton--fantasma" onClick={() => { setCategoria(""); setDesde(""); setHasta(""); }}>
              Quitar filtros
            </button>
          )}
        </div>

        {gastos.isError ? (
          <CargaFallida que="los gastos" error={gastos.error} alReintentar={() => void gastos.refetch()} />
        ) : !gastos.isSuccess ? (
          <p className="texto-2" role="status">Cargando…</p>
        ) : filas.length === 0 ? (
          <Vacio titulo={hayFiltros ? "Ningún gasto coincide con esos filtros" : "Todavía no hay gastos registrados"}>
            {usuario.puede_registrar && !hayFiltros ? "Registra reparaciones, regear, compras e ingredientes para ver adónde se va la plata." : undefined}
          </Vacio>
        ) : (
          <div className="tabla-envoltorio">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Fecha</th><th>Categoría</th><th>Descripción</th><th className="num">Monto</th>
                  {usuario.puede_registrar && <th><span className="sr-only">Acciones</span></th>}
                </tr>
              </thead>
              <tbody>
                {filas.map((gasto) => (
                  <tr key={gasto.id}>
                    <td className="texto-2">{fechaHora(gasto.fecha)}</td>
                    <td><Insignia>{CATEGORIAS_GASTO[gasto.categoria]}</Insignia></td>
                    <td>{gasto.descripcion || <span className="texto-3">—</span>}</td>
                    <td className="num"><Plata valor={gasto.monto} tamano="chica" /></td>
                    {usuario.puede_registrar && (
                      <td className="num">
                        <button
                          type="button"
                          className={`boton boton--chico ${confirmando === gasto.id ? "boton--peligro" : "boton--fantasma"}`}
                          aria-label={confirmando === gasto.id ? "Confirmar eliminación" : `Eliminar gasto de ${CATEGORIAS_GASTO[gasto.categoria]}`}
                          onClick={() => borrar(gasto.id)}
                        >
                          {confirmando === gasto.id ? "¿Seguro?" : <Icono nombre="borrar" tamano={16} />}
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={3}>{filas.length} {filas.length === 1 ? "gasto" : "gastos"}</td>
                  <td className="num"><Plata valor={total} tamano="chica" /></td>
                  {usuario.puede_registrar && <td />}
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </Bloque>

      <Cajon abierto={registrando} titulo="Registrar gasto" alCerrar={() => setRegistrando(false)}>
        <FormularioGasto alTerminar={() => setRegistrando(false)} />
      </Cajon>
      <DialogoImportar
        abierto={importando}
        titulo="Importar gastos"
        unidad="gastos"
        alCerrar={() => setImportando(false)}
        importar={(archivo) => importar.mutateAsync(archivo)}
        descargarPlantilla={() => void descargar("/api/gastos/plantilla")}
      />
    </div>
  );
}
