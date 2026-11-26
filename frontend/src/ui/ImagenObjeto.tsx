import { useState } from "react";

/** El servicio oficial de imágenes de Albion no entrega más de 217 px. */
const TAMANO_MAXIMO = 217;

/** Ícono oficial del objeto, con su encantamiento (@n) y su calidad (cambia el marco). */
export function urlImagenObjeto(baseId: string, encantamiento: number, calidad: number, tamano: number): string {
  const id = encodeURIComponent(baseId) + (encantamiento > 0 ? `@${encantamiento}` : "");
  const px = Math.min(Math.round(tamano), TAMANO_MAXIMO);
  return `https://render.albiononline.com/v1/item/${id}.png?quality=${calidad}&size=${px}`;
}

interface Props {
  baseId: string;
  encantamiento?: number;
  calidad?: number;
  tamano?: number;
}

/** Decorativa: el nombre del objeto siempre va escrito al lado, así que no se anuncia. */
export function ImagenObjeto({ baseId, encantamiento = 0, calidad = 1, tamano = 40 }: Props) {
  const src = urlImagenObjeto(baseId, encantamiento, calidad, tamano * 2); // el doble: nítida en pantallas densas
  const [fallida, setFallida] = useState<string | null>(null);

  if (fallida === src) {
    return <span className="imagen-objeto imagen-objeto--vacia" style={{ width: tamano, height: tamano }} aria-hidden="true" />;
  }
  return (
    <img
      className="imagen-objeto"
      src={src}
      alt=""
      width={tamano}
      height={tamano}
      loading="lazy"
      decoding="async"
      onError={() => setFallida(src)}
    />
  );
}
