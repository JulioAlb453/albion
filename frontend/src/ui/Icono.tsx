import type { ReactNode } from "react";

const FORMAS = {
  panel: (
    <>
      <rect x="3" y="3" width="8" height="8" rx="2" />
      <rect x="13" y="3" width="8" height="5" rx="2" />
      <rect x="13" y="10" width="8" height="11" rx="2" />
      <rect x="3" y="13" width="8" height="8" rx="2" />
    </>
  ),
  comparar: <path d="M7 4v16M7 4 3 8M7 4l4 4M17 20V4M17 20l-4-4M17 20l4-4" />,
  ventas: (
    <>
      <path d="M3 12V4h8l10 10-8 8z" />
      <circle cx="7.5" cy="8.5" r="1.2" />
    </>
  ),
  gastos: <path d="M3 7h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM3 7l12-3v3M16 14h2" />,
  reportes: <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />,
  alertas: <path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 7H4c0-1 2-2 2-7M10 20a2 2 0 0 0 4 0" />,
  sol: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  luna: <path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" />,
  salir: <path d="M9 4H5v16h4M16 8l4 4-4 4M20 12H9" />,
  entrar: <path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h11" />,
  mas: <path d="M12 5v14M5 12h14" />,
  descargar: <path d="M12 4v11M7 11l5 5 5-5M5 20h14" />,
  subir: <path d="M12 16V5M7 9l5-5 5 5M5 20h14" />,
  borrar: <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" />,
  cerrar: <path d="M6 6l12 12M18 6 6 18" />,
  buscar: (
    <>
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-4.5-4.5" />
    </>
  ),
  aviso: <path d="M12 3 22 21H2zM12 10v5M12 18h.01" />,
  check: <path d="m5 12 5 5 9-10" />,
  flecha: <path d="M5 12h14M13 6l6 6-6 6" />,
  vigilar: (
    <>
      <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
} satisfies Record<string, ReactNode>;

export type NombreIcono = keyof typeof FORMAS;

export function Icono({ nombre, tamano = 20 }: { nombre: NombreIcono; tamano?: number }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={tamano}
      height={tamano}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {FORMAS[nombre]}
    </svg>
  );
}
