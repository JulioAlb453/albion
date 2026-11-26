import { useEffect, useMemo, useState } from "react";
import { useDescargar, useEliminarVenta, useImportarVentas, useVentas } from "../api/consultas";
import { CIUDADES, TIPOS_VENTA, type Ciudad, type TipoVenta, type Venta } from "../api/tipos";
import { CargaFallida } from "../componentes/CargaFallida";
import { DialogoImportar } from "../componentes/DialogoImportar";
import { FormularioCorregirVenta } from "../componentes/FormularioCorregirVenta";
import { useSesion } from "../sesion/ContextoSesion";
import { useAvisos } from "../ui/Avisos";
import { Bloque, Plata, Vacio } from "../ui/Bloque";
import { Cajon } from "../ui/Cajon";
import { Icono } from "../ui/Icono";
import { ImagenObjeto } from "../ui/ImagenObjeto";
import { etiquetaCalidad, fechaHora, finDelDia, inicioDelDia, plataCompleta } from "../util/formato";

export function Ventas() {
  const { usuario } = useSesion();
  const { avisar } = useAvisos();
  const [ciudad, setCiudad] = useState<Ciudad | "">("");
  const [tipo, setTipo] = useState<TipoVenta | "">("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [importando, setImportando] = useState(false);
  const [confirmando, setConfirmando] = useState<number | null>(null);
  const [corrigiendo, setCorrigiendo] = useState<Venta | null>(null);

  const filtro = useMemo(
    () => ({ desde: desde ? inicioDelDia(desde) : undefined, hasta: hasta ? finDelDia(hasta) : undefined, ciudad, tipo }),
    [desde, hasta, ciudad, tipo],
  );
  const ventas = useVentas(filtro);
  const eliminar = useEliminarVenta();
  const importar = useImportarVentas();
  const descargar = useDescargar();

  // La confirmación de borrar se apaga sola: así un clic olvidado no deja un botón armado.
  useEffect(() => {
    if (confirmando === null) return;
    const temporizador = setTimeout(() => setConfirmando(null), 4_000);
    return () => clearTimeout(temporizador);
  }, [confirmando]);

  // La API las manda de la más vieja a la más nueva; en un registro lo reciente va arriba.
  const filas = useMemo(() => [...(ventas.data ?? [])].sort((a, b) => b.fecha.localeCompare(a.fecha)), [ventas.data]);
  const hayFiltros = Boolean(desde || hasta || ciudad || tipo);
  const totalNeto = filas.reduce((suma, v) => suma + v.neto, 0);
  const totalCargos = filas.reduce((suma, v) => suma + v.impuesto + v.tarifa_publicacion, 0);

  const borrar = (id: number) => {
    if (confirmando !== id) {
      setConfirmando(id);
      return;
    }
    eliminar.mutate(id, {
      onSuccess: () => avisar("Venta eliminada", "exito"),
      onError: (error) => avisar(error.message, "error"),
    });
    setConfirmando(null);
  };

  return (
    <div className="pila pila--grande">
      <Bloque
        titulo="Ventas registradas"
        columnas={12}
        accion={
          <div className="acciones-fila">
            <button type="button" className="boton" onClick={() => void descargar("/api/ventas/exportar", { ...filtro, formato: "csv" })}>
              <Icono nombre="descargar" tamano={18} /> Exportar CSV
            </button>
            <button type="button" className="boton" onClick={() => void descargar("/api/ventas/exportar", { ...filtro, formato: "xlsx" })}>
              <Icono nombre="descargar" tamano={18} /> Exportar Excel
            </button>
            {usuario.puede_registrar && (
              <button type="button" className="boton" onClick={() => setImportando(true)}>
                <Icono nombre="subir" tamano={18} /> Importar
              </button>
            )}
          </div>
        }
      >
        <div className="herramientas">
          <label className="campo">
            <span>Ciudad</span>
            <select value={ciudad} onChange={(e) => setCiudad(e.target.value as Ciudad | "")}>
              <option value="">Todas</option>
              {CIUDADES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label className="campo">
            <span>Tipo</span>
            <select value={tipo} onChange={(e) => setTipo(e.target.value as TipoVenta | "")}>
              <option value="">Todos</option>
              {(Object.keys(TIPOS_VENTA) as TipoVenta[]).map((t) => <option key={t} value={t}>{TIPOS_VENTA[t]}</option>)}
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
            <button type="button" className="boton boton--fantasma" onClick={() => { setCiudad(""); setTipo(""); setDesde(""); setHasta(""); }}>
              Quitar filtros
            </button>
          )}
        </div>

        {ventas.isError ? (
          <CargaFallida que="las ventas" error={ventas.error} alReintentar={() => void ventas.refetch()} />
        ) : !ventas.isSuccess ? (
          <p className="texto-2" role="status">Cargando…</p>
        ) : filas.length === 0 ? (
          <Vacio titulo={hayFiltros ? "Ninguna venta coincide con esos filtros" : "Todavía no hay ventas registradas"}>
            {usuario.puede_registrar && !hayFiltros ? "Registra la primera o importa tu historial desde un CSV." : undefined}
          </Vacio>
        ) : (
          <div className="tabla-envoltorio">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Fecha</th><th>Objeto</th><th>Ciudad</th><th>Tipo</th>
                  <th className="num">Cant.</th><th className="num">Precio</th><th className="num">Cargos</th><th className="num">Neto</th>
                  {usuario.puede_registrar && <th><span className="sr-only">Acciones</span></th>}
                </tr>
              </thead>
              <tbody>
                {filas.map((venta) => {
                  const nombre = venta.objeto.nombre ?? venta.objeto.base_id;
                  return (
                    <tr key={venta.id}>
                      <td className="texto-2">{fechaHora(venta.fecha)}</td>
                      <td>
                        <div className="tabla__objeto tabla__objeto--imagen">
                          <ImagenObjeto
                            baseId={venta.objeto.base_id} encantamiento={venta.objeto.encantamiento}
                            calidad={venta.objeto.calidad} tamano={36}
                          />
                          <span className="tabla__objeto-texto">
                            <span>{nombre}</span>
                            <span className="lista__detalle">
                              {venta.objeto.base_id.slice(0, 2)} ·{" "}
                              {venta.objeto.encantamiento > 0 ? `Encantamiento .${venta.objeto.encantamiento}` : "Sin encantar"} ·{" "}
                              {etiquetaCalidad(venta.objeto.calidad)}
                            </span>
                          </span>
                        </div>
                      </td>
                      <td>{venta.ciudad}</td>
                      <td>{TIPOS_VENTA[venta.tipo]}</td>
                      <td className="num">{venta.cantidad}</td>
                      <td className="num">{plataCompleta(venta.precio_unitario)}</td>
                      <td className="num">{plataCompleta(venta.impuesto + venta.tarifa_publicacion)}</td>
                      <td className="num"><Plata valor={venta.neto} tamano="chica" /></td>
                      {usuario.puede_registrar && (
                        <td className="num tabla__acciones">
                          <button
                            type="button"
                            className="boton boton--chico boton--fantasma"
                            aria-label={`Corregir venta de ${nombre}`}
                            title="Corregir encantamiento o calidad"
                            onClick={() => setCorrigiendo(venta)}
                          >
                            <Icono nombre="editar" tamano={16} />
                          </button>
                          <button
                            type="button"
                            className={`boton boton--chico ${confirmando === venta.id ? "boton--peligro" : "boton--fantasma"}`}
                            aria-label={confirmando === venta.id ? "Confirmar eliminación" : `Eliminar venta de ${nombre}`}
                            onClick={() => borrar(venta.id)}
                          >
                            {confirmando === venta.id ? "¿Seguro?" : <Icono nombre="borrar" tamano={16} />}
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={6}>{filas.length} {filas.length === 1 ? "venta" : "ventas"}</td>
                  <td className="num"><Plata valor={totalCargos} tamano="chica" /></td>
                  <td className="num"><Plata valor={totalNeto} tamano="chica" /></td>
                  {usuario.puede_registrar && <td />}
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </Bloque>

      <DialogoImportar
        abierto={importando}
        titulo="Importar ventas"
        unidad="ventas"
        alCerrar={() => setImportando(false)}
        importar={(archivo) => importar.mutateAsync(archivo)}
        descargarPlantilla={() => void descargar("/api/ventas/plantilla")}
      />
      <Cajon abierto={corrigiendo !== null} titulo="Corregir venta" alCerrar={() => setCorrigiendo(null)}>
        {corrigiendo && (
          <FormularioCorregirVenta key={corrigiendo.id} venta={corrigiendo} alTerminar={() => setCorrigiendo(null)} />
        )}
      </Cajon>
    </div>
  );
}
