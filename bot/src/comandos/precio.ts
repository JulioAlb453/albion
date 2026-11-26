import { antiguedad, plataCorta } from "../formato.js";
import type { Comparacion } from "../tipos.js";
import { COLOR, EFIMERO, OPCION_CALIDAD, OPCION_ENCANTAMIENTO, OPCION_OBJETO, type Comando } from "./comando.js";
import { consultar } from "./consulta.js";

function linea(c: Comparacion): string {
  const opciones = [c.directa, c.orden].filter((o) => o !== null);
  if (!opciones.length) return `**${c.ciudad}** — sin precios`;
  const mejor = opciones.sort((a, b) => b.neto - a.neto)[0]!;
  const etiqueta = mejor.tipo === "directa" ? "directa" : "orden";
  const base = `**${c.ciudad}** — ${plataCorta(mejor.neto_unitario)} netos (${etiqueta})`;
  return c.confiable ? base : `~~${base}~~ ⚠️ dato viejo, ${antiguedad(mejor.antiguedad_segundos)}`;
}

export const precio: Comando = {
  definicion: {
    name: "precio",
    description: "Mejor precio neto de un objeto por ciudad",
    options: [OPCION_OBJETO, OPCION_ENCANTAMIENTO, OPCION_CALIDAD],
  },
  async ejecutar(i, ctx) {
    await i.deferReply({ flags: EFIMERO });
    const { objeto, comparaciones } = await consultar(i, ctx, 1);
    const descripcion = comparaciones.length ? comparaciones.map(linea).join("\n") : "No hay precios de mercado para este objeto.";
    await i.editReply({
      embeds: [{
        title: objeto.nombre, description: descripcion, color: COLOR.info,
        footer: { text: "Netos tras impuesto y tarifa. Los datos viejos (más de 6 h) no cuentan como mejor opción." },
      }],
    });
  },
};
