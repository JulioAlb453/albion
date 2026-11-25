import { URL_API } from "../config";
import { Icono } from "../ui/Icono";

/** El regreso de Discord (y el 401 de la API) llegan como un código corto. */
const MENSAJES: Record<string, string> = {
  sin_acceso: "Tu cuenta de Discord no tiene un rol del gremio. Pide a un oficial que te lo asigne.",
  cancelado: "Cancelaste el inicio de sesión.",
  estado_invalido: "El inicio de sesión expiró. Inténtalo de nuevo.",
  codigo_invalido: "Discord rechazó el código de acceso. Inténtalo de nuevo.",
  discord_no_disponible: "No se pudo hablar con Discord. Inténtalo en un momento.",
  sesion_vencida: "Tu sesión venció. Vuelve a entrar.",
};

export function Entrar({ error }: { error?: string }) {
  return (
    <main className="entrada">
      <section className="bloque bloque--acento entrada__tarjeta">
        <span className="marca__logo marca__logo--grande" aria-hidden="true">G</span>
        <div>
          <h1>Gremio · Ventas</h1>
          <p className="texto-2">Registro de ventas, impuestos y balance del gremio en Albion Online.</p>
        </div>
        {error && (
          <p role="alert" className="caja caja--error">
            {MENSAJES[error] ?? `No se pudo iniciar sesión (${error}).`}
          </p>
        )}
        <a className="boton boton--primario boton--grande" href={`${URL_API}/api/auth/discord/login`}>
          <Icono nombre="entrar" /> Entrar con Discord
        </a>
        <p className="nota">Solo pedimos tu identidad: no vemos tu correo ni tu contraseña.</p>
      </section>
    </main>
  );
}
