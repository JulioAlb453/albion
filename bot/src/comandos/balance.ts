import { plataCorta, signo } from "../formato.js";
import { COLOR, EFIMERO, type Comando } from "./comando.js";

export const balance: Comando = {
  definicion: { name: "balance", description: "Saldo del gremio y resultado de ventas y gastos" },
  async ejecutar(i, ctx) {
    await i.deferReply({ flags: EFIMERO });
    const [inicial, evolucion, reporte] = await Promise.all([ctx.api.saldoInicial(), ctx.api.evolucion(), ctx.api.reportes()]);
    if (!inicial && !evolucion.length) {
      await i.editReply("Todavía no hay saldo inicial. Un administrador debe configurarlo en la web.");
      return;
    }
    const saldo = evolucion.at(-1)?.saldo ?? inicial!.monto;
    await i.editReply({
      embeds: [{
        title: "Balance del gremio", color: COLOR.bien,
        fields: [
          { name: "Saldo", value: plataCorta(saldo), inline: true },
          { name: "Ventas netas", value: plataCorta(reporte.ventas_netas), inline: true },
          { name: "Gastos", value: plataCorta(reporte.gastos_totales), inline: true },
          { name: "Resultado", value: signo(reporte.resultado), inline: true },
          { name: "Impuestos y tarifas", value: plataCorta(reporte.impuestos.total), inline: true },
        ],
      }],
    });
  },
};
