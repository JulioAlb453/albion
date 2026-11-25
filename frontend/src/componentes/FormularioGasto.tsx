import { useState, type FormEvent } from "react";
import { useRegistrarGasto } from "../api/consultas";
import { CATEGORIAS_GASTO, type CategoriaGasto } from "../api/tipos";
import { useAvisos } from "../ui/Avisos";

/** Registra un gasto del gremio: reparaciones, regear, compras, ingredientes… */
export function FormularioGasto({ alTerminar }: { alTerminar: () => void }) {
  const [categoria, setCategoria] = useState<CategoriaGasto>("reparaciones");
  const [descripcion, setDescripcion] = useState("");
  const [monto, setMonto] = useState("");
  const [fecha, setFecha] = useState("");
  const registrar = useRegistrarGasto();
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
          avisar("Gasto registrado", "exito");
          alTerminar();
        },
      },
    );
  };

  return (
    <form className="formulario" onSubmit={enviar}>
      <label className="campo">
        <span>Categoría</span>
        <select value={categoria} onChange={(e) => setCategoria(e.target.value as CategoriaGasto)}>
          {(Object.keys(CATEGORIAS_GASTO) as CategoriaGasto[]).map((clave) => (
            <option key={clave} value={clave}>{CATEGORIAS_GASTO[clave]}</option>
          ))}
        </select>
      </label>

      <label className={`campo${faltaDescripcion && descripcion === "" && monto !== "" ? " campo--error" : ""}`}>
        <span>Descripción {categoria === "otros" ? "" : "(opcional)"}</span>
        <input type="text" maxLength={200} placeholder="Reparaciones tras el ZvZ" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
        {faltaDescripcion && <span className="campo__ayuda">Para «Otros» escribe una descripción.</span>}
      </label>

      <label className="campo">
        <span>Monto en plata</span>
        <input type="number" min={1} step={1} inputMode="numeric" value={monto} onChange={(e) => setMonto(e.target.value)} />
      </label>

      <label className="campo">
        <span>Fecha y hora (opcional)</span>
        <input type="datetime-local" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        <span className="campo__ayuda">Si la dejas vacía se usa el momento actual.</span>
      </label>

      {registrar.isError && <p role="alert" className="caja caja--error">{registrar.error.message}</p>}

      <div>
        <button type="submit" className="boton boton--primario boton--grande" disabled={!valido || registrar.isPending}>
          {registrar.isPending ? "Guardando…" : "Guardar gasto"}
        </button>
      </div>
    </form>
  );
}
