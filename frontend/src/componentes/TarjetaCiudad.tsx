import { TIPOS_VENTA, type Ciudad, type Comparacion, type Opcion, type TipoVenta } from "../api/tipos";
import { Insignia, Plata } from "../ui/Bloque";
import { antiguedad, plataCompleta, signo } from "../util/formato";

interface Props {
  comparacion: Comparacion;
  /** Es la mejor ciudad de la lista (y su dato es reciente). */
  esMejor: boolean;
  puedeRegistrar: boolean;
  cantidad: number;
  alRegistrar: (ciudad: Ciudad, tipo: TipoVenta, precioUnitario: number) => void;
}

function BloqueOpcion({
  ciudad, tipo, opcion, ganadora, cantidad, puedeRegistrar, alRegistrar, vacio,
}: {
  ciudad: Ciudad;
  tipo: TipoVenta;
  opcion: Opcion | null;
  ganadora: boolean;
  cantidad: number;
  puedeRegistrar: boolean;
  alRegistrar: Props["alRegistrar"];
  vacio: string;
}) {
  return (
    <div
      role="group"
      aria-label={TIPOS_VENTA[tipo]}
      data-ganadora={String(ganadora)}
      className={`opcion${ganadora ? " opcion--mejor" : ""}`}
    >
      <div className="opcion__titulo">{TIPOS_VENTA[tipo]}</div>
      {opcion ? (
        <>
          <Plata valor={opcion.neto} tamano="media" />
          {cantidad > 1 && <p className="opcion__detalle">{plataCompleta(opcion.neto_unitario)} por unidad</p>}
          <p className="opcion__detalle">
            Precio {plataCompleta(opcion.precio_unitario)} · cargos {plataCompleta(opcion.impuesto + opcion.tarifa_publicacion)}
          </p>
          <p className="opcion__detalle texto-3">
            <span>{antiguedad(opcion.antiguedad_segundos)}</span>
            {!opcion.confiable && <span className="aviso-texto"> · dato viejo</span>}
          </p>
          {puedeRegistrar && (
            <button
              type="button"
              className="boton boton--chico"
              aria-label={`Registrar venta ${tipo === "directa" ? "directa" : "por orden"} en ${ciudad}`}
              onClick={() => alRegistrar(ciudad, tipo, opcion.precio_unitario)}
            >
              Registrar
            </button>
          )}
        </>
      ) : (
        <p className="opcion__detalle texto-3">{vacio}</p>
      )}
    </div>
  );
}

/** Lo que paga una ciudad por el objeto: venta directa contra orden de venta. */
export function TarjetaCiudad({ comparacion, esMejor, puedeRegistrar, cantidad, alRegistrar }: Props) {
  const { ciudad, es_del_gremio, directa, orden, mejor, confiable, diferencia_orden_vs_directa: diferencia } = comparacion;
  const clases = ["bloque", "ciudad", !confiable && "ciudad--vieja", esMejor && "ciudad--mejor"].filter(Boolean).join(" ");
  const compartido = { ciudad, cantidad, puedeRegistrar, alRegistrar };

  return (
    <article className={clases}>
      <header className="ciudad__cabecera">
        <h3 className="ciudad__nombre">{ciudad}</h3>
        <div className="fila fila--junta">
          {es_del_gremio && <Insignia tono="acento">Tu isla</Insignia>}
          {esMejor && <Insignia tono="positivo">Mejor opción</Insignia>}
          {!confiable && <Insignia tono="aviso">Dato viejo</Insignia>}
        </div>
      </header>

      <BloqueOpcion {...compartido} tipo="directa" opcion={directa} ganadora={mejor === "directa"} vacio="Sin órdenes de compra registradas" />
      <BloqueOpcion {...compartido} tipo="orden" opcion={orden} ganadora={mejor === "orden"} vacio="Sin órdenes de venta registradas" />

      {diferencia !== null && (
        <p className="ciudad__diferencia">
          La orden deja <strong className={diferencia >= 0 ? "positivo" : "negativo"}>{signo(diferencia)}</strong>{" "}
          {diferencia >= 0 ? "más" : "menos"} que vender directo
        </p>
      )}
    </article>
  );
}
