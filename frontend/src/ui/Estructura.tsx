import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useRegistro } from "../componentes/ContextoRegistro";
import { useSesion } from "../sesion/ContextoSesion";
import { Icono, type NombreIcono } from "./Icono";
import { useTema } from "./tema";

const SECCIONES: { ruta: string; texto: string; icono: NombreIcono }[] = [
  { ruta: "/", texto: "Panel", icono: "panel" },
  { ruta: "/comparador", texto: "Comparador", icono: "comparar" },
  { ruta: "/ventas", texto: "Ventas", icono: "ventas" },
  { ruta: "/gastos", texto: "Gastos", icono: "gastos" },
  { ruta: "/reportes", texto: "Reportes", icono: "reportes" },
  { ruta: "/alertas", texto: "Alertas", icono: "alertas" },
];

function Avatar({ discordId, hash, nombre }: { discordId: string; hash: string | null; nombre: string }) {
  if (hash) {
    return <img className="avatar" alt="" src={`https://cdn.discordapp.com/avatars/${discordId}/${hash}.png?size=64`} />;
  }
  return <span className="avatar" aria-hidden="true">{nombre.charAt(0).toUpperCase()}</span>;
}

/** El marco de la aplicación: barra lateral, barra superior y el contenido de cada sección. */
export function Estructura() {
  const { usuario, cerrarSesion } = useSesion();
  const { abrirVenta } = useRegistro();
  const { tema, alternar } = useTema();
  const { pathname } = useLocation();
  const seccion = SECCIONES.find((s) => (s.ruta === "/" ? pathname === "/" : pathname.startsWith(s.ruta)));

  return (
    <div className="app">
      <aside className="lateral">
        <div className="marca">
          <span className="marca__logo" aria-hidden="true">G</span>
          <span>Gremio · Ventas</span>
        </div>
        <nav className="nav" aria-label="Principal">
          {SECCIONES.map(({ ruta, texto, icono }) => (
            <NavLink key={ruta} to={ruta} end={ruta === "/"}>
              <Icono nombre={icono} />
              {texto}
            </NavLink>
          ))}
        </nav>
        <p className="lateral__pie">Las fechas del balance usan la hora del juego (UTC).</p>
      </aside>

      <div className="principal">
        <header className="barra">
          <h1>{seccion?.texto ?? "Panel"}</h1>
          <span className="separador" />
          {usuario.puede_registrar && (
            <button className="boton boton--primario" onClick={() => abrirVenta()}>
              <Icono nombre="mas" /> Registrar venta
            </button>
          )}
          <button
            className="boton boton--icono"
            aria-label={`Cambiar a tema ${tema === "oscuro" ? "claro" : "oscuro"}`}
            onClick={alternar}
          >
            <Icono nombre={tema === "oscuro" ? "sol" : "luna"} />
          </button>
          <div className="usuario">
            <Avatar discordId={usuario.discord_id} hash={usuario.avatar_hash} nombre={usuario.nombre} />
            <div>
              <div className="usuario__nombre">{usuario.nombre}</div>
              <div className="usuario__rol">{usuario.rol === "admin" ? "Administrador" : "Solo consulta"}</div>
            </div>
          </div>
          <button className="boton boton--fantasma boton--icono" aria-label="Salir" onClick={cerrarSesion}>
            <Icono nombre="salir" />
          </button>
        </header>
        <main className="contenido">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
