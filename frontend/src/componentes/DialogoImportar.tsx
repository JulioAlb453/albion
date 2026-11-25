import { useId, useState } from "react";
import { ErrorApi, type ErrorFila } from "../api/cliente";
import type { ResultadoImportacion } from "../api/tipos";
import { Cajon } from "../ui/Cajon";
import { Icono } from "../ui/Icono";

interface Props {
  abierto: boolean;
  titulo: string;
  unidad: "ventas" | "gastos";
  alCerrar: () => void;
  importar: (archivo: File) => Promise<ResultadoImportacion>;
  descargarPlantilla: () => void;
}

type Estado =
  | { tipo: "libre" }
  | { tipo: "importando" }
  | { tipo: "listo"; importadas: number }
  | { tipo: "rechazado"; errores: ErrorFila[] }
  | { tipo: "fallo"; mensaje: string };

const SINGULAR = { ventas: "venta", gastos: "gasto" } as const;

function Contenido({ unidad, alCerrar, importar, descargarPlantilla }: Omit<Props, "abierto" | "titulo">) {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [estado, setEstado] = useState<Estado>({ tipo: "libre" });
  const idArchivo = useId();

  const enviar = async () => {
    if (!archivo) return;
    setEstado({ tipo: "importando" });
    try {
      const resultado = await importar(archivo);
      setEstado({ tipo: "listo", importadas: resultado.importadas });
    } catch (error) {
      if (error instanceof ErrorApi && error.errores) setEstado({ tipo: "rechazado", errores: error.errores });
      else setEstado({ tipo: "fallo", mensaje: error instanceof Error ? error.message : "No se pudo importar el archivo" });
    }
  };

  return (
    <>
      <ol className="pasos">
        <li className="pila">
          <span>Descarga la plantilla y llénala con una fila por cada {SINGULAR[unidad]}. Puedes abrirla en Excel y guardarla como CSV.</span>
          <div>
            <button type="button" className="boton" onClick={descargarPlantilla}>
              <Icono nombre="descargar" tamano={18} /> Descargar plantilla
            </button>
          </div>
        </li>
        <li className="pila">
          <label className="campo" htmlFor={idArchivo}>
            <span>Archivo CSV</span>
          </label>
          <input
            id={idArchivo}
            type="file"
            accept=".csv,text/csv"
            onChange={(evento) => {
              setArchivo(evento.target.files?.[0] ?? null);
              setEstado({ tipo: "libre" });
            }}
          />
          <p className="campo__ayuda">Es todo o nada: si una fila tiene un problema no se importa ninguna.</p>
        </li>
      </ol>

      {estado.tipo === "listo" && (
        <p role="status" className="caja">
          {estado.importadas === 1
            ? `Se importó 1 ${SINGULAR[unidad]}.`
            : `Se importaron ${estado.importadas} ${unidad}.`}
        </p>
      )}
      {estado.tipo === "fallo" && <p role="alert" className="caja caja--error">{estado.mensaje}</p>}
      {estado.tipo === "rechazado" && (
        <div className="pila">
          <p role="status" className="caja caja--error">
            <strong>No se importó nada.</strong> Corrige estas filas y vuelve a intentarlo.
          </p>
          <div className="tabla-envoltorio">
            <table className="tabla">
              <thead>
                <tr><th>Fila</th><th>Problema</th></tr>
              </thead>
              <tbody>
                {estado.errores.map((error) => (
                  <tr key={`${error.fila}-${error.mensaje}`}>
                    <td className="num">{error.fila}</td>
                    <td>{error.mensaje}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="campo__ayuda">La fila 1 es el encabezado, así que los datos empiezan en la 2.</p>
        </div>
      )}

      <div className="fila">
        {estado.tipo === "listo" ? (
          <button type="button" className="boton boton--primario" onClick={alCerrar}>Cerrar</button>
        ) : (
          <button type="button" className="boton boton--primario" disabled={!archivo || estado.tipo === "importando"} onClick={() => void enviar()}>
            {estado.tipo === "importando" ? "Importando…" : "Importar"}
          </button>
        )}
      </div>
    </>
  );
}

/** Importar un CSV completo, con la plantilla a mano y los errores fila por fila. */
export function DialogoImportar({ abierto, titulo, alCerrar, ...resto }: Props) {
  return (
    <Cajon abierto={abierto} titulo={titulo} alCerrar={alCerrar}>
      {/* se desmonta al cerrar: cada vez que se abre empieza sin archivo ni resultados */}
      <Contenido alCerrar={alCerrar} {...resto} />
    </Cajon>
  );
}
