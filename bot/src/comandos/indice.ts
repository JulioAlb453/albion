import { balance } from "./balance.js";
import type { Comando } from "./comando.js";
import { comparar } from "./comparar.js";
import { gasto } from "./gasto.js";
import { precio } from "./precio.js";
import { venta } from "./venta.js";

export const COMANDOS: Comando[] = [precio, comparar, balance, venta, gasto];
