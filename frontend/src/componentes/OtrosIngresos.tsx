import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useEliminarIngreso, useIngresos, useRegistrarIngreso } from "../api/consultas";
import { CATEGORIAS_INGRESO, type CategoriaIngreso } from "../api/tipos";
import { useSesion } from "../sesion/ContextoSesion";
import { useAvisos } from "../ui/Avisos";
import { Bloque, Insignia, Plata, Vacio } from "../ui/Bloque";
import { Cajon } from "../ui/Cajon";
import { Icono } from "../ui/Icono";
import { fechaHora } from "../util/formato";
import { CargaFallida } from "./CargaFallida";

/** Plata que entra al gremio sin vender objetos: donaciones, territorios, botín en plata… */
export function OtrosIngresos() {
  const { usuario } = useSesion();
  const { avisar } = useAvisos();
  const ingresos = useIngresos();
  const eliminar = useEliminarIngreso();
  const [registrando, setRegistrando] = useState(false);
  const [confirmando, setConfirmando] = useState<number | null>(null);

  useEffect(() => {
    if (confirmando === null) return;
    const temporizador = setTimeout(() => setConfirmando(null), 4_000);
    return () => clearTimeout(temporizador);
  }, [confirmando]);

  const filas = useMemo(() => [...(ingresos.data ?? [])].sort((a, b) => b.fecha.localeCompare(a.fecha)), [ingresos.data]);
  const total = filas.reduce((suma, i) => suma + i.monto, 0);

  const borrar = (id: number) => {
    if (confirmando !== id) return setConfirmando(id);
    eliminar.mutate(id, {
      onSuccess: () => avisar("Ingreso eliminado", "exito"),
      onError: (error) => avisar(error.message, "error"),
    });
    setConfirmando(null);
  };

  return (
    <Bloque
      titulo="Otros ingresos"
      columnas={12}
      accion={
        usuario.puede_registrar ? (
          <button type="button" className="boton boton--primario" onClick={() => setRegistrando(true)}>
            <Icono nombre="mas" tamano={18} /> Registrar ingreso
          </button>
        ) : undefined
      }
    >
      {ingresos.isError ? (
        <CargaFallida que="los ingresos" error={ingresos.error} alReintentar={() => void ingresos.refetch()} />
      ) : !ingresos.isSuccess ? (
        <p className="texto-2" role="status">Cargando…</p>
      ) : filas.length === 0 ? (
        <Vacio titulo="Todavía no hay otros ingresos">
          Donaciones, territorios, bolsas de plata: lo que entra al gremio sin vender objetos.
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
              {filas.map((ingreso) => (
                <tr key={ingreso.id}>
                  <td className="texto-2">{fechaHora(ingreso.fecha)}</td>
                  <td><Insignia tono="positivo">{CATEGORIAS_INGRESO[ingreso.categoria]}</Insignia></td>
                  <td>{ingreso.descripcion || <span className="texto-3">—</span>}</td>
                  <td className="num"><Plata valor={ingreso.monto} tamano="chica" /></td>
                  {usuario.puede_registrar && (
                    <td className="num">
                      <button
                        type="button"
                        className={`boton boton--chico ${confirmando === ingreso.id ? "boton--peligro" : "boton--fantasma"}`}
                        aria-label={confirmando === ingreso.id ? "Confirmar eliminación" : `Eliminar ingreso de ${CATEGORIAS_INGRESO[ingreso.categoria]}`}
                        onClick={() => borrar(ingreso.id)}
                      >
                        {confirmando === ingreso.id ? "¿Seguro?" : <Icono nombre="borrar" tamano={16} />}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={3}>{filas.length} {filas.length === 1 ? "ingreso" : "ingresos"}</td>
                <td className="num"><Plata valor={total} tamano="chica" /></td>
                {usuario.puede_registrar && <td />}
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      <Cajon abierto={registrando} titulo="Registrar ingreso" alCerrar={() => setRegistrando(false)}>
        <FormularioIngreso alTerminar={() => setRegistrando(false)} />
      </Cajon>
    </Bloque>
  );
}

function FormularioIngreso({ alTerminar }: { alTerminar: () => void }) {
  const [categoria, setCategoria] = useState<CategoriaIngreso>("donacion");
  const [descripcion, setDescripcion] = useState("");
  const [monto, setMonto] = useState("");
  const [fecha, setFecha] = useState("");
  const registrar = useRegistrarIngreso();
  const { avisar } = useAvisos();

  const montoValido = monto !== "" && Number.isInteger(Number(monto)) && Number(monto) > 0;
  const faltaDescripcion = categoria === "otros" && descripcion.trim() === "";
  const valido = montoValido && !faltaDescripcion;

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    if (!valido) return;
    registrar.mutate(
      {
        categoria,
        descripcion: descripcion.trim(),
        monto: Number(monto),
        ...(fecha ? { fecha: new Date(fecha).toISOString() } : {}),
      },
      {
        onSuccess: () => {
          avisar("Ingreso registrado", "exito");
          alTerminar();
        },
      },
    );
  };

  return (
    <form className="formulario" onSubmit={enviar}>
      <label className="campo">
        <span>Categoría</span>
        <select value={categoria} onChange={(e) => setCategoria(e.target.value as CategoriaIngreso)}>
          {(Object.keys(CATEGORIAS_INGRESO) as CategoriaIngreso[]).map((clave) => (
            <option key={clave} value={clave}>{CATEGORIAS_INGRESO[clave]}</option>
          ))}
        </select>
      </label>

      <label className="campo">
        <span>Monto en plata</span>
        <input type="number" min={1} step={1} inputMode="numeric" value={monto} onChange={(e) => setMonto(e.target.value)} />
      </label>

      <label className="campo">
        <span>Descripción {categoria === "otros" ? "" : "(opcional)"}</span>
        <input type="text" maxLength={200} placeholder="Quién donó, qué territorio…" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
        {faltaDescripcion && <span className="campo__ayuda">Para «Otros» escribe una descripción.</span>}
      </label>

      <label className="campo">
        <span>Fecha y hora (opcional)</span>
        <input type="datetime-local" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        <span className="campo__ayuda">Si la dejas vacía se usa el momento actual.</span>
      </label>

      {registrar.isError && <p role="alert" className="caja caja--error">{registrar.error.message}</p>}

      <div>
        <button type="submit" className="boton boton--primario boton--grande" disabled={!valido || registrar.isPending}>
          {registrar.isPending ? "Guardando…" : "Guardar ingreso"}
        </button>
      </div>
    </form>
  );
}
