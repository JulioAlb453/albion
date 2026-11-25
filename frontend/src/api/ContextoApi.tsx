import { createContext, useContext } from "react";
import type { Cliente } from "./cliente";

const ContextoApi = createContext<Cliente | null>(null);

export const ProveedorApi = ContextoApi.Provider;

export function useCliente(): Cliente {
  const cliente = useContext(ContextoApi);
  if (!cliente) throw new Error("useCliente se usó fuera de ProveedorSesion");
  return cliente;
}
