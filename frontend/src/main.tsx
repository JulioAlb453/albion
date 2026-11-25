import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { iniciarDesdeUrl } from "./sesion/sesion";
import { ponerTema, temaInicial } from "./ui/tema";
import "./estilos/tokens.css";
import "./estilos/estilos.css";

// Antes de dibujar nada: el tema (para que no parpadee) y el resultado del inicio de sesión que
// viene en la dirección (para que el token no se quede en la barra del navegador).
ponerTema(temaInicial());
const { error } = iniciarDesdeUrl();

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <App errorInicial={error} />
  </StrictMode>,
);
