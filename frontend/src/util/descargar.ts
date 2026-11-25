/** Hace que el navegador guarde un archivo que ya tenemos en memoria. */
export function guardarArchivo(archivo: Blob, nombre: string): void {
  const direccion = URL.createObjectURL(archivo);
  const enlace = document.createElement("a");
  enlace.href = direccion;
  enlace.download = nombre;
  document.body.append(enlace);
  enlace.click();
  enlace.remove();
  setTimeout(() => URL.revokeObjectURL(direccion), 1_000);
}
