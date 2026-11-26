import type { InteraccionComando } from "../interacciones.js";
import type { Comparacion, Contexto, ObjetoCatalogo } from "../tipos.js";

/** Lo común de /precio y /comparar: leer el objeto y pedir las comparaciones. */
export async function consultar(i: InteraccionComando, ctx: Contexto, cantidad: number) {
  const baseId = i.options.getString("objeto") ?? "";
  const objeto: ObjetoCatalogo = await ctx.api.obtenerObjeto(baseId);
  // cada objeto admite lo suyo (un tomo no tiene calidad, un recurso .2 es siempre .2): se ajusta lo escrito
  const pedido = i.options.getInteger("encantamiento") ?? objeto.encantamiento_min;
  const encantamiento = Math.min(Math.max(pedido, objeto.encantamiento_min), objeto.encantamiento_max);
  const calidad = objeto.tiene_calidad ? (i.options.getInteger("calidad") ?? 1) : 1;
  const comparaciones = await ctx.api.comparar({ base_id: baseId, encantamiento, calidad, cantidad });
  return { objeto, comparaciones: ordenar(comparaciones) };
}

/** Black Market primero, luego datos confiables por neto, y al final los viejos. */
export function ordenar(lista: Comparacion[]): Comparacion[] {
  const mejorNeto = (c: Comparacion) => Math.max(c.directa?.neto ?? 0, c.orden?.neto ?? 0);
  return [...lista].sort((a, b) => {
    if ((a.ciudad === "Black Market") !== (b.ciudad === "Black Market")) return a.ciudad === "Black Market" ? -1 : 1;
    if (a.confiable !== b.confiable) return a.confiable ? -1 : 1;
    return mejorNeto(b) - mejorNeto(a);
  });
}
