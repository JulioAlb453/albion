import { createContext, useContext } from "react";
import type { Ciudad, ObjetoCatalogo, TipoVenta } from "../api/tipos";

/** Lo que ya se sabe de la venta cuando se abre el formulario desde otra pantalla. */
export interface PrefillVenta {
  objeto?: ObjetoCatalogo;
  encantamiento?: number;
  calidad?: number;
  cantidad?: number;
  ciudad?: Ciudad;
  tipo?: TipoVenta;
  precio_unitario?: number;
}

export interface ValorRegistro {
  /** Abre el formulario de registrar una venta, con datos ya cargados si se tienen. */
  abrirVenta: (prefill?: PrefillVenta) => void;
}

/** Por defecto no hace nada: así las pantallas se pueden probar sin el formulario. */
export const ContextoRegistro = createContext<ValorRegistro>({ abrirVenta: () => {} });

export function useRegistro(): ValorRegistro {
  return useContext(ContextoRegistro);
}
