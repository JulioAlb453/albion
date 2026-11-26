import { plataCorta } from "../formato.js";
import { CATEGORIAS_GASTO, type CategoriaGasto } from "../tipos.js";
import { COLOR, EFIMERO, TIPO_OPCION, type Comando } from "./comando.js";

export const gasto: Comando = {
  definicion: {
    name: "gasto",
    description: "Registrar un gasto (solo administradores)",
    options: [
      {
        name: "categoria", description: "En qué se gastó", type: TIPO_OPCION.texto, required: true,
        choices: Object.entries(CATEGORIAS_GASTO).map(([value, name]) => ({ name, value })),
      },
      { name: "monto", description: "Plata gastada", type: TIPO_OPCION.entero, required: true, min_value: 1 },
      { name: "descripcion", description: "Detalle opcional", type: TIPO_OPCION.texto },
    ],
  },
  async ejecutar(i, ctx) {
    await i.deferReply({ flags: EFIMERO });
    const categoria = (i.options.getString("categoria") ?? "otros") as CategoriaGasto;
    const registrado = await ctx.api.registrarGasto({
      categoria, monto: i.options.getInteger("monto") ?? 0, descripcion: i.options.getString("descripcion") ?? "",
    });
    await i.editReply(`Gasto registrado: ${plataCorta(registrado.monto)}.`);
    await i.followUp({
      embeds: [{
        title: "Gasto registrado", color: COLOR.aviso,
        description: `**${i.user.globalName || i.user.username}** registró un gasto en ${CATEGORIAS_GASTO[registrado.categoria]}.`,
        fields: [
          { name: "Monto", value: plataCorta(registrado.monto), inline: true },
          ...(registrado.descripcion ? [{ name: "Detalle", value: registrado.descripcion, inline: true }] : []),
        ],
      }],
    });
  },
};
