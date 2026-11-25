import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import { ErrorApi } from "./api/cliente";
import { ProveedorRegistro } from "./componentes/ProveedorRegistro";
import { Alertas } from "./paginas/Alertas";
import { Comparador } from "./paginas/Comparador";
import { Gastos } from "./paginas/Gastos";
import { Panel } from "./paginas/Panel";
import { Reportes } from "./paginas/Reportes";
import { Ventas } from "./paginas/Ventas";
import { ProveedorSesion } from "./sesion/ProveedorSesion";
import { ProveedorAvisos } from "./ui/Avisos";
import { Estructura } from "./ui/Estructura";

function Rutas() {
  return (
    <Routes>
      <Route element={<Estructura />}>
        <Route index element={<Panel />} />
        <Route path="comparador" element={<Comparador />} />
        <Route path="ventas" element={<Ventas />} />
        <Route path="gastos" element={<Gastos />} />
        <Route path="reportes" element={<Reportes />} />
        <Route path="alertas" element={<Alertas />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export function App({ errorInicial }: { errorInicial?: string }) {
  const [consultas] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            // Un error del cliente (4xx) o de red no se arregla repitiéndolo; uno del servidor, quizá sí.
            retry: (intentos, error) => error instanceof ErrorApi && error.status >= 500 && intentos < 1,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={consultas}>
      <HashRouter>
        <ProveedorAvisos>
          <ProveedorSesion errorInicial={errorInicial}>
            <ProveedorRegistro>
              <Rutas />
            </ProveedorRegistro>
          </ProveedorSesion>
        </ProveedorAvisos>
      </HashRouter>
    </QueryClientProvider>
  );
}
