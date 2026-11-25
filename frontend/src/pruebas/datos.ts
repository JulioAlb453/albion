import type { Ciudad, Comparacion, Objeto, ObjetoCatalogo, Opcion, TipoVenta, Venta } from "../api/tipos";

export const ESPADA: ObjetoCatalogo = {
  base_id: "T6_MAIN_SWORD", nombre: "Espada ancha del maestro", categoria: "arma", tiene_calidad: true,
};
export const ARMADURA: ObjetoCatalogo = {
  base_id: "T6_ARMOR_PLATE_SET1", nombre: "Armadura de soldado del maestro", categoria: "armadura", tiene_calidad: true,
};
export const ARTEFACTO: ObjetoCatalogo = {
  base_id: "T4_ARTEFACT_2H_BOW_KEEPER", nombre: "Hueso tallado del iniciado", categoria: "artefacto", tiene_calidad: false,
};

export const OBJETO_ESPADA: Objeto = {
  base_id: "T6_MAIN_SWORD", nombre: "Espada ancha del maestro", etiqueta: "T6.2", encantamiento: 2, calidad: 4,
};

/** Una opción de venta con cifras coherentes con 4 % de impuesto y 2.5 % de tarifa de publicación. */
export function opcion(tipo: TipoVenta, netoUnitario: number, extra: Partial<Opcion> = {}): Opcion {
  const precio = Math.round(netoUnitario / (tipo === "directa" ? 0.96 : 0.935));
  return {
    tipo,
    precio_unitario: precio,
    bruto: precio,
    impuesto: Math.round(precio * 0.04),
    tarifa_publicacion: tipo === "orden" ? Math.round(precio * 0.025) : 0,
    neto: netoUnitario,
    neto_unitario: netoUnitario,
    fecha_dato: "2026-11-25T11:55:00Z",
    antiguedad_segundos: 300,
    confiable: true,
    ...extra,
  };
}

export function comparacion(
  ciudad: Ciudad,
  { directa = null, orden = null, confiable = true }: { directa?: Opcion | null; orden?: Opcion | null; confiable?: boolean },
): Comparacion {
  const mejor = [directa, orden].filter((o): o is Opcion => o !== null).sort((a, b) => b.neto - a.neto)[0];
  return {
    ciudad,
    es_del_gremio: ["Fort Sterling", "Lymhurst", "Caerleon"].includes(ciudad),
    directa,
    orden,
    mejor: mejor?.tipo ?? null,
    confiable,
    diferencia_orden_vs_directa: directa && orden ? orden.neto - directa.neto : null,
  };
}

export function venta(extra: Partial<Venta> = {}): Venta {
  return {
    id: 1, objeto: OBJETO_ESPADA, ciudad: "Lymhurst", tipo: "directa", cantidad: 2, precio_unitario: 100_000,
    fecha: "2026-11-25T18:00:00Z", bruto: 200_000, impuesto: 8_000, tarifa_publicacion: 0, neto: 192_000,
    ...extra,
  };
}
