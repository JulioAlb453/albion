import type { Comparacion, Objeto, ObjetoCatalogo, Opcion, TipoVenta, Venta } from "../tipos.js";

export const ESPADA: ObjetoCatalogo = {
  base_id: "T6_MAIN_SWORD", nombre: "Espada ancha del maestro", categoria: "arma", tiene_calidad: true,
  encantamiento_min: 0, encantamiento_max: 4,
};
export const ARTEFACTO: ObjetoCatalogo = {
  base_id: "T4_ARTEFACT_2H_BOW_KEEPER", nombre: "Hueso tallado del iniciado", categoria: "artefacto", tiene_calidad: false,
  encantamiento_min: 0, encantamiento_max: 0,
};
export const OBJETO_ESPADA: Objeto = {
  base_id: "T6_MAIN_SWORD", nombre: "Espada ancha del maestro", etiqueta: "T6.2", encantamiento: 2, calidad: 4,
};

/** Una opción de venta con cifras coherentes con 4 % de impuesto y 2.5 % de tarifa de publicación. */
export function opcion(tipo: TipoVenta, netoUnitario: number, extra: Partial<Opcion> = {}): Opcion {
  const precio = Math.round(netoUnitario / (tipo === "directa" ? 0.96 : 0.935));
  return {
    tipo, precio_unitario: precio, bruto: precio, impuesto: Math.round(precio * 0.04),
    tarifa_publicacion: tipo === "orden" ? Math.round(precio * 0.025) : 0,
    neto: netoUnitario, neto_unitario: netoUnitario, fecha_dato: "2026-11-25T11:55:00Z",
    antiguedad_segundos: 300, confiable: true, ...extra,
  };
}

export function comparacion(
  ciudad: Comparacion["ciudad"],
  { directa = null, orden = null, confiable = true }: { directa?: Opcion | null; orden?: Opcion | null; confiable?: boolean },
): Comparacion {
  const mejor = [directa, orden].filter((o): o is Opcion => o !== null).sort((a, b) => b.neto - a.neto)[0];
  return {
    ciudad, es_del_gremio: ["Fort Sterling", "Lymhurst", "Caerleon"].includes(ciudad),
    directa, orden, mejor: mejor?.tipo ?? null, confiable,
    diferencia_orden_vs_directa: directa && orden ? orden.neto - directa.neto : null,
  };
}

export const COMPARACIONES = [
  comparacion("Black Market", { directa: opcion("directa", 144_000) }),
  comparacion("Caerleon", { orden: opcion("orden", 112_200) }),
  comparacion("Fort Sterling", { directa: opcion("directa", 86_400), orden: opcion("orden", 93_500) }),
  comparacion("Thetford", { directa: opcion("directa", 900_000, { confiable: false, antiguedad_segundos: 18 * 3_600 }), confiable: false }),
];

export const VENTA: Venta = {
  id: 1, objeto: OBJETO_ESPADA, ciudad: "Fort Sterling", tipo: "orden", cantidad: 1, precio_unitario: 100_000,
  fecha: "2026-11-25T12:00:00Z", bruto: 100_000, impuesto: 4_000, tarifa_publicacion: 2_500, neto: 93_500,
};
