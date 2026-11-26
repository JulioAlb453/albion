import { useEffect, useState, type FormEvent } from "react";
import { useAsignarPago, useEliminarPago, usePagosSemanales, useRegistrarPago } from "../api/consultas";
import { ESTADOS_PAGO, type EstadoPago, type PagoSemanal } from "../api/tipos";
import { useSesion } from "../sesion/ContextoSesion";
import { useAvisos } from "../ui/Avisos";
import { Bloque, Insignia, Plata, Vacio } from "../ui/Bloque";
import { Cajon } from "../ui/Cajon";
import { Icono } from "../ui/Icono";
import { diaCorto, fechaHora, plataCorta } from "../util/formato";
import { etiquetaSemana, hoyServidor, lunesDe, moverSemanas } from "../util/semana";
import { CargaFallida } from "./CargaFallida";

const TONO: Record<EstadoPago, "aviso" | "info" | "positivo" | "negativo"> = {
  pendiente: "aviso", parcial: "info", pagado: "positivo", no_reclamado: "negativo",
};

/**
 * Pagos semanales a miembros (lunes a domingo, hora del servidor). Solo lo pagado sale del saldo;
 * lo que no se cobra antes de que termine el domingo se queda en el gremio.
 */
export function PagosSemanales() {
  const { usuario } = useSesion();
  const { avisar } = useAvisos();
  const [semana, setSemana] = useState(() => lunesDe(hoyServidor()));
  const pagos = usePagosSemanales(semana);
  const eliminar = useEliminarPago();
  const [asignando, setAsignando] = useState(false);
  const [pagando, setPagando] = useState<PagoSemanal | null>(null);
  const [confirmando, setConfirmando] = useState<number | null>(null);

  useEffect(() => {
    if (confirmando === null) return;
    const temporizador = setTimeout(() => setConfirmando(null), 4_000);
    return () => clearTimeout(temporizador);
  }, [confirmando]);

  const filas = pagos.data ?? [];
  const asignado = filas.reduce((s, p) => s + p.monto, 0);
  const pagado = filas.reduce((s, p) => s + p.pagado, 0);
  const noReclamado = filas.reduce((s, p) => s + p.no_reclamado, 0);
  const esActual = semana === lunesDe(hoyServidor());

  const borrar = (id: number) => {
    if (confirmando !== id) return setConfirmando(id);
    eliminar.mutate(id, {
      onSuccess: () => avisar("Pago eliminado", "exito"),
      onError: (error) => avisar(error.message, "error"),
    });
    setConfirmando(null);
  };

  return (
    <Bloque
      titulo="Pagos semanales"
      columnas={12}
      accion={
        usuario.puede_registrar ? (
          <button type="button" className="boton boton--primario" onClick={() => setAsignando(true)}>
            <Icono nombre="mas" tamano={18} /> Asignar pago
          </button>
        ) : undefined
      }
    >
      <div className="semana">
        <button type="button" className="boton boton--fantasma boton--icono" aria-label="Semana anterior" onClick={() => setSemana(moverSemanas(semana, -1))}>
          <span aria-hidden="true">‹</span>
        </button>
        <div className="semana__titulo">
          <strong>{etiquetaSemana(semana)}</strong>
          <span className="texto-3">{esActual ? "Semana actual" : "Lunes a domingo, hora del servidor"}</span>
        </div>
        <button type="button" className="boton boton--fantasma boton--icono" aria-label="Semana siguiente" onClick={() => setSemana(moverSemanas(semana, 1))}>
          <span aria-hidden="true">›</span>
        </button>
        {!esActual && (
          <button type="button" className="boton boton--chico" onClick={() => setSemana(lunesDe(hoyServidor()))}>Ir a la actual</button>
        )}
      </div>

      {pagos.isError ? (
        <CargaFallida que="los pagos" error={pagos.error} alReintentar={() => void pagos.refetch()} />
      ) : !pagos.isSuccess ? (
        <p className="texto-2" role="status">Cargando…</p>
      ) : filas.length === 0 ? (
        <Vacio titulo="Esta semana no se asignaron pagos">
          {usuario.puede_registrar ? "Asigna a cada miembro lo que le toca; luego registra lo que se le vaya pagando." : undefined}
        </Vacio>
      ) : (
        <>
          <div className="tabla-envoltorio">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Miembro</th><th className="num">Asignado</th><th className="num">Pagado</th><th>Estado</th><th>Día del pago</th>
                  {usuario.puede_registrar && <th><span className="sr-only">Acciones</span></th>}
                </tr>
              </thead>
              <tbody>
                {filas.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <div className="tabla__objeto">
                        <span>{p.miembro}</span>
                        {p.descripcion && <span className="lista__detalle">{p.descripcion}</span>}
                      </div>
                    </td>
                    <td className="num"><Plata valor={p.monto} tamano="chica" /></td>
                    <td className="num"><Plata valor={p.pagado} tamano="chica" /></td>
                    <td><Insignia tono={TONO[p.estado]}>{ESTADOS_PAGO[p.estado]}</Insignia></td>
                    <td className="texto-2">{p.fecha_pago ? fechaHora(p.fecha_pago) : "—"}</td>
                    {usuario.puede_registrar && (
                      <td className="num tabla__acciones">
                        <button
                          type="button"
                          className="boton boton--chico boton--fantasma"
                          aria-label={`Registrar pago de ${p.miembro}`}
                          title="Registrar o corregir lo pagado"
                          onClick={() => setPagando(p)}
                        >
                          <Icono nombre="editar" tamano={16} />
                        </button>
                        <button
                          type="button"
                          className={`boton boton--chico ${confirmando === p.id ? "boton--peligro" : "boton--fantasma"}`}
                          aria-label={confirmando === p.id ? "Confirmar eliminación" : `Eliminar pago de ${p.miembro}`}
                          onClick={() => borrar(p.id)}
                        >
                          {confirmando === p.id ? "¿Seguro?" : <Icono nombre="borrar" tamano={16} />}
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td>{filas.length} {filas.length === 1 ? "miembro" : "miembros"}</td>
                  <td className="num"><Plata valor={asignado} tamano="chica" /></td>
                  <td className="num"><Plata valor={pagado} tamano="chica" /></td>
                  <td colSpan={usuario.puede_registrar ? 3 : 2} />
                </tr>
              </tfoot>
            </table>
          </div>
          {noReclamado > 0 && (
            <p className="nota">
              Se dejaron de cobrar <strong>{plataCorta(noReclamado)}</strong> esta semana: queda para el gremio.
            </p>
          )}
        </>
      )}

      <Cajon abierto={asignando} titulo="Asignar pago" alCerrar={() => setAsignando(false)}>
        <FormularioAsignar semana={semana} alTerminar={() => setAsignando(false)} />
      </Cajon>
      <Cajon abierto={pagando !== null} titulo="Registrar pago" alCerrar={() => setPagando(null)}>
        {pagando && <FormularioPago key={pagando.id} pago={pagando} alTerminar={() => setPagando(null)} />}
      </Cajon>
    </Bloque>
  );
}

const enteroPositivo = (texto: string) => texto !== "" && Number.isInteger(Number(texto)) && Number(texto) > 0;

function FormularioAsignar({ semana, alTerminar }: { semana: string; alTerminar: () => void }) {
  const [miembro, setMiembro] = useState("");
  const [monto, setMonto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const asignar = useAsignarPago();
  const { avisar } = useAvisos();
  const valido = miembro.trim() !== "" && enteroPositivo(monto);

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    if (!valido) return;
    asignar.mutate(
      { miembro: miembro.trim(), monto: Number(monto), semana, descripcion: descripcion.trim() },
      {
        onSuccess: () => {
          avisar("Pago asignado", "exito");
          alTerminar();
        },
      },
    );
  };

  return (
    <form className="formulario" onSubmit={enviar}>
      <p className="texto-2">Semana del {etiquetaSemana(semana)}.</p>
      <label className="campo">
        <span>Miembro</span>
        <input type="text" maxLength={100} placeholder="Nombre en el juego" value={miembro} onChange={(e) => setMiembro(e.target.value)} />
      </label>
      <label className="campo">
        <span>Monto asignado</span>
        <input type="number" min={1} step={1} inputMode="numeric" value={monto} onChange={(e) => setMonto(e.target.value)} />
      </label>
      <label className="campo">
        <span>Descripción (opcional)</span>
        <input type="text" maxLength={200} placeholder="Por qué se le paga" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
      </label>
      {asignar.isError && <p role="alert" className="caja caja--error">{asignar.error.message}</p>}
      <div>
        <button type="submit" className="boton boton--primario boton--grande" disabled={!valido || asignar.isPending}>
          {asignar.isPending ? "Guardando…" : "Guardar"}
        </button>
      </div>
    </form>
  );
}

function FormularioPago({ pago, alTerminar }: { pago: PagoSemanal; alTerminar: () => void }) {
  const [pagado, setPagado] = useState(pago.pagado > 0 ? String(pago.pagado) : "");
  const [fecha, setFecha] = useState("");
  const registrar = useRegistrarPago();
  const { avisar } = useAvisos();

  const numero = Number(pagado);
  const formatoValido = pagado !== "" && Number.isInteger(numero) && numero >= 0;
  const deMas = formatoValido && numero > pago.monto;
  const valido = formatoValido && !deMas;

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    if (!valido) return;
    registrar.mutate(
      { id: pago.id, pagado: numero, ...(fecha ? { fecha_pago: new Date(fecha).toISOString() } : {}) },
      {
        onSuccess: () => {
          avisar("Pago registrado", "exito");
          alTerminar();
        },
      },
    );
  };

  return (
    <form className="formulario" onSubmit={enviar}>
      <div>
        <p className="lista__titulo">{pago.miembro}</p>
        <p className="texto-2">Asignado: {plataCorta(pago.monto)} · semana del {etiquetaSemana(pago.semana)}</p>
      </div>

      <label className={`campo${deMas ? " campo--error" : ""}`}>
        <span>Total pagado hasta ahora</span>
        <input type="number" min={0} max={pago.monto} step={1} inputMode="numeric" value={pagado} onChange={(e) => setPagado(e.target.value)} />
        {deMas ? (
          <span className="campo__ayuda">No puede pasar de lo asignado ({plataCorta(pago.monto)}).</span>
        ) : (
          <span className="campo__ayuda">Si fue un pago parcial, pon lo que lleva cobrado; luego lo puedes corregir.</span>
        )}
      </label>
      <div>
        <button type="button" className="boton boton--chico" onClick={() => setPagado(String(pago.monto))}>Pago completo</button>
      </div>

      <label className="campo">
        <span>Día del pago (opcional)</span>
        <input type="datetime-local" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        <span className="campo__ayuda">
          Si lo dejas vacío se usa el momento actual. Debe caer entre el {diaCorto(pago.semana)} y el {diaCorto(pago.fin_semana)}.
        </span>
      </label>

      {registrar.isError && <p role="alert" className="caja caja--error">{registrar.error.message}</p>}
      <div>
        <button type="submit" className="boton boton--primario boton--grande" disabled={!valido || registrar.isPending}>
          {registrar.isPending ? "Guardando…" : "Guardar"}
        </button>
      </div>
    </form>
  );
}
