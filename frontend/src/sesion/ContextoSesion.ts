import { createContext, useContext } from "react";
import type { Usuario } from "../api/tipos";

export interface ValorSesion {
  usuario: Usuario;
  cerrarSesion: () => void;
}

export const ContextoSesion = createContext<ValorSesion | null>(null);

export function useSesion(): ValorSesion {
  const valor = useContext(ContextoSesion);
  if (!valor) throw new Error("useSesion se usó fuera de ProveedorSesion");
  return valor;
}
