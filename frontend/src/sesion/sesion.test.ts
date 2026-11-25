import {
  borrarToken,
  expiracionDe,
  guardarToken,
  iniciarDesdeUrl,
  leerFragmento,
  leerToken,
} from "./sesion";

/** Un JWT con la forma real: solo importa la carga del medio. */
function jwt(carga: object): string {
  const b64 = (o: object) => btoa(JSON.stringify(o)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return `${b64({ alg: "HS256" })}.${b64(carga)}.firma`;
}
const enSegundos = (ms: number) => Math.floor(ms / 1000);
const enUnaHora = () => jwt({ sub: "1", exp: enSegundos(Date.now() + 3_600_000) });
const hacePoco = () => jwt({ sub: "1", exp: enSegundos(Date.now() - 1_000) });

describe("leerFragmento", () => {
  it("lee el token y los errores del regreso de Discord", () => {
    expect(leerFragmento("#token=abc.def.ghi")).toEqual({ token: "abc.def.ghi" });
    expect(leerFragmento("#error=sin_acceso")).toEqual({ error: "sin_acceso" });
  });

  it("ignora las rutas de la aplicación y lo vacío", () => {
    expect(leerFragmento("#/ventas")).toEqual({});
    expect(leerFragmento("")).toEqual({});
    expect(leerFragmento("#")).toEqual({});
  });
});

describe("expiracionDe", () => {
  it("saca la fecha de vencimiento en milisegundos", () => {
    expect(expiracionDe(jwt({ exp: 1_800_000_000 }))).toBe(1_800_000_000_000);
  });

  it.each(["", "basura", "a.b.c", jwt({ sin: "exp" })])("devuelve null con %j", (token) => {
    expect(expiracionDe(token)).toBeNull();
  });
});

describe("token guardado", () => {
  it("se guarda y se lee mientras no venza", () => {
    const token = enUnaHora();
    guardarToken(token);
    expect(leerToken()).toBe(token);
  });

  it("uno vencido no se devuelve y se borra", () => {
    guardarToken(hacePoco());
    expect(leerToken()).toBeNull();
    expect(localStorage.length).toBe(0);
  });

  it("se puede borrar", () => {
    guardarToken(enUnaHora());
    borrarToken();
    expect(leerToken()).toBeNull();
  });

  it("sin nada guardado no hay sesión", () => {
    expect(leerToken()).toBeNull();
  });
});

describe("iniciarDesdeUrl", () => {
  it("guarda el token del fragmento y deja la dirección limpia", () => {
    const token = enUnaHora();
    window.location.hash = `#token=${token}`;
    expect(iniciarDesdeUrl()).toEqual({ error: undefined });
    expect(leerToken()).toBe(token);
    expect(window.location.hash).toBe("#/");  // el token no se queda en la barra de direcciones
  });

  it("devuelve el error del regreso y también limpia la dirección", () => {
    window.location.hash = "#error=sin_acceso";
    expect(iniciarDesdeUrl()).toEqual({ error: "sin_acceso" });
    expect(window.location.hash).toBe("#/");
    expect(leerToken()).toBeNull();
  });

  it("no toca una ruta normal de la aplicación", () => {
    window.location.hash = "#/ventas";
    expect(iniciarDesdeUrl()).toEqual({ error: undefined });
    expect(window.location.hash).toBe("#/ventas");
  });

  it("un token ya vencido no inicia sesión", () => {
    window.location.hash = `#token=${hacePoco()}`;
    iniciarDesdeUrl();
    expect(leerToken()).toBeNull();
  });
});
