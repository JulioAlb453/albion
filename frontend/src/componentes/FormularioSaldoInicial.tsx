import { useState, type FormEvent } from "react";
import { useGuardarSaldoInicial } from "../api/consultas";
import { useAvisos } from "../ui/Avisos";
import { diaLocalHaceDias } from "../util/formato";

/** Cuánta plata tiene el gremio el día en que empieza el registro. */
export function FormularioSaldoInicial() {
  const [monto, setMonto] = useState("");
  const [fecha, setFecha] = useState(() => diaLocalHaceDias(0));
  const guardar = useGuardarSaldoInicial();
  const { avisar } = useAvisos();

  const valido = monto !== "" && Number.isInteger(Number(monto)) && Number(monto) >= 0 && fecha !== "";

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    guardar.mutate(
      { monto: Number(monto), fecha },
      {
        onSuccess: () => avisar("Saldo inicial guardado", "exito"),
        onError: (error) => avisar(error.message, "error"),
      },
    );
  };

  return (
    <form className="formulario" onSubmit={enviar}>
      <div>
        <p className="vacio__titulo">Configura tu saldo inicial</p>
        <p className="texto-2">
          Es la plata con la que arranca el registro. Las ventas y gastos anteriores a esa fecha no cuentan.
        </p>
      </div>
      <div className="rejilla-2">
        <label className="campo">
          <span>Monto en plata</span>
          <input type="number" min={0} step={1} inputMode="numeric" placeholder="120000000" value={monto} onChange={(e) => setMonto(e.target.value)} />
        </label>
        <label className="campo">
          <span>Fecha de inicio</span>
          <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        </label>
      </div>
      <div>
        <button type="submit" className="boton boton--primario" disabled={!valido || guardar.isPending}>
          {guardar.isPending ? "Guardando…" : "Guardar saldo inicial"}
        </button>
      </div>
    </form>
  );
}
