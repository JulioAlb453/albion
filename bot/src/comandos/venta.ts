import { etiquetaCalidad, plataCorta } from "../formato.js";
import { CIUDADES, TIPOS_VENTA, type Ciudad, type TipoVenta } from "../tipos.js";
import { COLOR, EFIMERO, OPCION_CALIDAD, OPCION_ENCANTAMIENTO, OPCION_OBJETO, TIPO_OPCION, type Comando } from "./comando.js";

export const venta: Comando = {
  definicion: {
    name: "venta",
    description: "Registrar una venta (solo administradores)",
    options: [
      OPCION_OBJETO,
      { name: "ciudad", description: "Dónde se vendió", type: TIPO_OPCION.texto, required: true, choices: CIUDADES.map((c) => ({ name: c, value: c })) },
      {
        name: "tipo", description: "Cómo se vendió", type: TIPO_OPCION.texto, required: true,
        choices: Object.entries(TIPOS_VENTA).map(([value, name]) => ({ name, value })),
      },
      { name: "cantidad", description: "Unidades vendidas", type: TIPO_OPCION.entero, required: true, min_value: 1, max_value: 999 },
      { name: "precio", description: "Precio unitario en plata", type: TIPO_OPCION.entero, required: true, min_value: 1 },
      OPCION_ENCANTAMIENTO,
      OPCION_CALIDAD,
    ],
  },
  async ejecutar(i, ctx) {
    await i.deferReply({ flags: EFIMERO });
    const registrada = await ctx.api.registrarVenta({
      base_id: i.options.getString("objeto") ?? "",
      encantamiento: i.options.getInteger("encantamiento") ?? 0,
      calidad: i.options.getInteger("calidad") ?? 1,
      ciudad: (i.options.getString("ciudad") ?? "") as Ciudad,
      tipo: (i.options.getString("tipo") ?? "") as TipoVenta,
      cantidad: i.options.getInteger("cantidad") ?? 1,
      precio_unitario: i.options.getInteger("precio") ?? 0,
    });
    const o = registrada.objeto;
    await i.editReply(`Venta registrada: ${plataCorta(registrada.neto)} netos.`);
    await i.followUp({
      embeds: [{
        title: "Venta registrada", color: COLOR.bien,
        description: `**${i.user.globalName || i.user.username}** vendió ${registrada.cantidad} × ${o.nombre ?? o.base_id} ${o.etiqueta} (${etiquetaCalidad(o.calidad)}) en ${registrada.ciudad}.`,
        fields: [
          { name: "Tipo", value: TIPOS_VENTA[registrada.tipo], inline: true },
          { name: "Bruto", value: plataCorta(registrada.bruto), inline: true },
          { name: "Neto", value: plataCorta(registrada.neto), inline: true },
        ],
      }],
    });
  },
};
