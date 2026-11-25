import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorApi } from "../api/cliente";
import type { ResultadoImportacion } from "../api/tipos";
import { montarPagina } from "../pruebas/utiles";
import { DialogoImportar } from "./DialogoImportar";

const ARCHIVO = new File(["fecha,objeto\n"], "ventas.csv", { type: "text/csv" });

function montar(importar = vi.fn<(f: File) => Promise<ResultadoImportacion>>().mockResolvedValue({ importadas: 2, errores: [] })) {
  const alCerrar = vi.fn();
  const descargarPlantilla = vi.fn();
  montarPagina(
    <DialogoImportar
      abierto
      titulo="Importar ventas"
      unidad="ventas"
      alCerrar={alCerrar}
      importar={importar}
      descargarPlantilla={descargarPlantilla}
    />,
  );
  return { importar, alCerrar, descargarPlantilla };
}
const botonImportar = () => screen.getByRole("button", { name: /^importar$/i });

describe("DialogoImportar", () => {
  it("cerrado no muestra nada", () => {
    montarPagina(
      <DialogoImportar abierto={false} titulo="Importar ventas" unidad="ventas" alCerrar={() => {}} importar={vi.fn()} descargarPlantilla={() => {}} />,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("explica los pasos y ofrece la plantilla", async () => {
    const { descargarPlantilla } = montar();
    expect(screen.getByRole("dialog", { name: /importar ventas/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /descargar plantilla/i }));
    expect(descargarPlantilla).toHaveBeenCalledOnce();
  });

  it("no deja importar hasta elegir un archivo", async () => {
    montar();
    expect(botonImportar()).toBeDisabled();
    await userEvent.upload(screen.getByLabelText(/archivo/i), ARCHIVO);
    expect(botonImportar()).toBeEnabled();
  });

  it("al importar con éxito dice cuántas se importaron", async () => {
    const { importar } = montar();
    await userEvent.upload(screen.getByLabelText(/archivo/i), ARCHIVO);
    await userEvent.click(botonImportar());
    expect(importar).toHaveBeenCalledWith(ARCHIVO);
    expect(await screen.findByText(/se importaron 2 ventas/i)).toBeInTheDocument();
  });

  it("si el archivo se rechaza lista cada fila mala con su motivo y dice que no se importó nada", async () => {
    const errores = [
      { fila: 3, mensaje: "ciudad: 'Narnia' no es válido" },
      { fila: 7, mensaje: "cantidad: 'abc' no es un número entero" },
    ];
    montar(vi.fn().mockRejectedValue(new ErrorApi(422, "El archivo tiene 2 filas con problemas", errores)));
    await userEvent.upload(screen.getByLabelText(/archivo/i), ARCHIVO);
    await userEvent.click(botonImportar());

    expect(await screen.findByText(/no se importó nada/i)).toBeInTheDocument();
    const filas = within(screen.getByRole("table")).getAllByRole("row").slice(1);
    expect(filas.map((f) => f.textContent)).toEqual([
      "3ciudad: 'Narnia' no es válido",
      "7cantidad: 'abc' no es un número entero",
    ]);
  });

  it("un fallo que no es del archivo se muestra como alerta", async () => {
    montar(vi.fn().mockRejectedValue(new ErrorApi(0, "No se pudo conectar con el servidor")));
    await userEvent.upload(screen.getByLabelText(/archivo/i), ARCHIVO);
    await userEvent.click(botonImportar());
    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo conectar con el servidor");
  });

  it("mientras importa bloquea el botón para no mandarlo dos veces", async () => {
    let terminar: (r: ResultadoImportacion) => void = () => {};
    const importar = vi.fn(() => new Promise<ResultadoImportacion>((resolver) => { terminar = resolver; }));
    montar(importar);
    await userEvent.upload(screen.getByLabelText(/archivo/i), ARCHIVO);
    await userEvent.click(botonImportar());
    expect(screen.getByRole("button", { name: /importando/i })).toBeDisabled();
    terminar({ importadas: 1, errores: [] });
    await waitFor(() => expect(screen.getByText(/se importó 1 venta\b/i)).toBeInTheDocument());
  });
});
