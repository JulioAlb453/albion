/** Lo que se ve en un bloque cuando su dato no llegó: el resto de la pantalla sigue funcionando. */
export function CargaFallida({ que, error, alReintentar }: { que: string; error: Error; alReintentar: () => void }) {
  return (
    <div className="caja caja--error pila" role="alert">
      <p>No se pudo cargar {que}.</p>
      <p className="texto-2">{error.message}</p>
      <div>
        <button type="button" className="boton" onClick={alReintentar}>Reintentar</button>
      </div>
    </div>
  );
}
