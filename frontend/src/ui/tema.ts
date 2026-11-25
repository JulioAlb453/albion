import { useCallback, useEffect, useState } from "react";

export type Tema = "oscuro" | "claro";
const CLAVE = "gremio.tema";

/** Lo que eligió la persona; si no eligió nada, lo que prefiere su sistema; y si no, oscuro. */
export function temaInicial(): Tema {
  try {
    const guardado = localStorage.getItem(CLAVE);
    if (guardado === "claro" || guardado === "oscuro") return guardado;
  } catch {
    // sin almacenamiento: se sigue con la preferencia del sistema
  }
  return window.matchMedia?.("(prefers-color-scheme: light)").matches ? "claro" : "oscuro";
}

/** Solo lo pone en la página (sin recordarlo). */
export function ponerTema(tema: Tema): void {
  document.documentElement.dataset.tema = tema;
}

/** Lo pone y lo recuerda: es lo que pasa cuando la persona usa el interruptor. */
export function aplicarTema(tema: Tema): void {
  ponerTema(tema);
  try {
    localStorage.setItem(CLAVE, tema);
  } catch {
    // no se pudo recordar; vale para esta visita
  }
}

export function useTema() {
  const [tema, setTema] = useState<Tema>(temaInicial);
  useEffect(() => ponerTema(tema), [tema]);
  const alternar = useCallback(() => {
    const siguiente: Tema = tema === "oscuro" ? "claro" : "oscuro";
    aplicarTema(siguiente);
    setTema(siguiente);
  }, [tema]);
  return { tema, alternar };
}
