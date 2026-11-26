import { antiguedad, plataCorta, signo } from "../formato.js";
import type { Comparacion } from "../tipos.js";
import { COLOR, EFIMERO, OPCION_CALIDAD, OPCION_ENCANTAMIENTO, OPCION_OBJETO, TIPO_OPCION, type Comando } from "./comando.js";
import { consultar } from "./consulta.js";

function linea(c: Comparacion): string {
  const partes = [
    c.directa ? `Directa ${plataCorta(c.directa.neto)}` : null,
    c.orden ? `Orden ${plataCorta(c.orden.neto)}` : null,
  ].filter((p): p is string => p !== null);
  if (!partes.length) return `**${c.ciudad}** — sin precios`;
  if (c.diferencia_orden_vs_directa !== null) partes.push(`Δ ${signo(c.diferencia_orden_vs_directa)}`);
  const base = `**${c.ciudad}** — ${partes.join(" · ")}`;
  const dato = (c.directa ?? c.orden)!;
  return c.confiable ? base : `~~${base}~~ ⚠️ ${antiguedad(dato.antiguedad_segundos)}`;
}

export const comparar: Comando = {
  definicion: {
    name: "comparar",
    description: "Compara venta directa y orden de venta en cada ciudad",
    options: [
      OPCION_OBJETO,
      { name: "cantidad", description: "Unidades a vender (por defecto 1)", type: TIPO_OPCION.entero, min_value: 1, max_value: 999 },
      OPCION_ENCANTAMIENTO,
      OPCION_CALIDAD,
    ],
  },
  async ejecutar(i, ctx) {
    await i.deferReply({ flags: EFIMERO });
    const cantidad = i.options.getInteger("cantidad") ?? 1;
    const { objeto, comparaciones } = await consultar(i, ctx, cantidad);
    const descripcion = comparaciones.length ? comparaciones.map(linea).join("\n") : "No hay precios de mercado para este objeto.";
    await i.editReply({
      embeds: [{
        title: `${objeto.nombre} × ${cantidad}`, description: descripcion, color: COLOR.info,
        footer: { text: "Δ = orden − directa. Positivo: conviene la orden de venta." },
      }],
    });
  },
};
