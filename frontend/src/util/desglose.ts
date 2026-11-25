import type { TipoVenta } from "../api/tipos";

// Tasas con premium activo, en milésimas (40 = 4 %). Solo sirven para la vista previa de un
// formulario: el cálculo que cuenta lo hace siempre el servidor.
const IMPUESTO_DE_VENTA = 40;
const TARIFA_DE_PUBLICACION = 25;

export interface Desglose {
  bruto: number;
  impuesto: number;
  tarifa: number;
  neto: number;
}

/** Redondeo con enteros, mitad hacia arriba, igual que el servidor (sin errores de coma flotante). */
const porMil = (monto: number, tasa: number) => Math.floor((monto * tasa + 500) / 1000);

export function calcularDesglose(precio: number, cantidad: number, tipo: TipoVenta, tarifaExtra = 0): Desglose {
  const bruto = precio * cantidad;
  const impuesto = porMil(bruto, IMPUESTO_DE_VENTA);
  const tarifa = tipo === "orden" ? porMil(bruto, TARIFA_DE_PUBLICACION) + tarifaExtra : 0;
  return { bruto, impuesto, tarifa, neto: bruto - impuesto - tarifa };
}
