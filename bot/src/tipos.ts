// Las formas de lo que devuelve y recibe la API; salen de los esquemas.py de cada módulo del backend.

export type Rol = "admin" | "general";

export interface Usuario {
  discord_id: string;
  nombre: string;
  avatar_hash: string | null;
  rol: Rol;
  puede_registrar: boolean;
}

export const CIUDADES = [
  "Fort Sterling", "Lymhurst", "Caerleon", "Bridgewatch", "Martlock", "Thetford", "Brecilien", "Black Market",
] as const;
export type Ciudad = (typeof CIUDADES)[number];

/** Donde el gremio tiene isla. La API también lo manda (`es_del_gremio`) en las comparaciones. */
export const CIUDADES_GREMIO: readonly Ciudad[] = ["Fort Sterling", "Lymhurst", "Caerleon"];

export type TipoVenta = "directa" | "orden";
export const TIPOS_VENTA: Record<TipoVenta, string> = { directa: "Venta directa", orden: "Orden de venta" };

export const CATEGORIAS_GASTO = {
  compra_equipo: "Compra de equipo",
  reparaciones: "Reparaciones",
  reequipamiento_builds: "Reequipamiento de builds",
  ingredientes_comida: "Ingredientes de comida",
  otros: "Otros",
} as const;
export type CategoriaGasto = keyof typeof CATEGORIAS_GASTO;

/** Las secciones del mercado del juego (las mismas que el backend). */
export const CATEGORIAS_OBJETO = {
  arma: "Armas",
  armadura: "Armaduras",
  capa: "Capas",
  bolsa: "Bolsas",
  montura: "Monturas",
  consumible: "Consumibles",
  recurso: "Recursos",
  artefacto: "Artefactos",
  recoleccion: "Recolección",
  granja: "Granja",
  mobiliario: "Mobiliario",
  apariencia: "Apariencia",
  otro: "Otros",
} as const;
export type CategoriaObjeto = keyof typeof CATEGORIAS_OBJETO;

export interface Objeto {
  base_id: string;
  nombre: string | null;
  etiqueta: string; // T6.2
  encantamiento: number;
  calidad: number;
}

export interface ObjetoCatalogo {
  base_id: string;
  nombre: string;
  categoria: CategoriaObjeto;
  tiene_calidad: boolean;
  /** Rango de encantamiento que se puede elegir; si son iguales es fijo (p. ej. un recurso .2). */
  encantamiento_min: number;
  encantamiento_max: number;
}

export interface Venta {
  id: number;
  objeto: Objeto;
  ciudad: Ciudad;
  tipo: TipoVenta;
  cantidad: number;
  precio_unitario: number;
  fecha: string;
  bruto: number;
  impuesto: number;
  tarifa_publicacion: number;
  neto: number;
}

export interface NuevaVenta {
  base_id: string;
  encantamiento: number;
  calidad: number;
  ciudad: Ciudad;
  tipo: TipoVenta;
  cantidad: number;
  precio_unitario: number;
  fecha?: string;
  tarifa_extra?: number;
}

export interface Gasto {
  id: number;
  categoria: CategoriaGasto;
  descripcion: string;
  monto: number;
  fecha: string;
}

export interface NuevoGasto {
  categoria: CategoriaGasto;
  descripcion: string;
  monto: number;
  fecha?: string;
}

export interface Opcion {
  tipo: TipoVenta;
  precio_unitario: number;
  bruto: number;
  impuesto: number;
  tarifa_publicacion: number;
  neto: number;
  neto_unitario: number;
  fecha_dato: string;
  antiguedad_segundos: number;
  confiable: boolean;
}

export interface Comparacion {
  ciudad: Ciudad;
  es_del_gremio: boolean;
  directa: Opcion | null;
  orden: Opcion | null; // el Black Market no admite órdenes de venta
  mejor: TipoVenta | null;
  confiable: boolean;
  diferencia_orden_vs_directa: number | null;
}

export interface SaldoInicial {
  monto: number;
  fecha: string; // "2026-11-25"
}

export interface PuntoBalance {
  fecha: string;
  ingresos: number;
  gastos: number;
  saldo: number;
}

export interface GananciaObjeto {
  objeto: Objeto;
  unidades: number;
  bruto: number;
  impuesto: number;
  tarifa_publicacion: number;
  neto: number;
}

export interface Reportes {
  ganancia_por_objeto: GananciaObjeto[];
  impuestos: { impuesto_venta: number; tarifa_publicacion: number; total: number };
  gastos_por_categoria: { categoria: CategoriaGasto; monto: number }[];
  ventas_netas: number;
  gastos_totales: number;
  resultado: number;
}

export interface Seguimiento {
  id: number;
  objeto: Objeto;
  ciudad_referencia: Ciudad;
  porcentaje_minimo: number | null;
  neto_minimo: number | null;
}

export interface NuevoSeguimiento {
  base_id: string;
  encantamiento: number;
  calidad: number;
  ciudad_referencia: Ciudad;
  porcentaje_minimo?: number;
  neto_minimo?: number;
}

export interface Alerta {
  id: number;
  seguimiento_id: number;
  objeto: Objeto;
  ciudad: Ciudad;
  tipo: TipoVenta;
  neto_unitario: number;
  neto_referencia: number | null;
  motivo: string;
  fecha: string;
}

export interface ResultadoImportacion {
  importadas: number;
  errores: { fila: number; mensaje: string }[];
}

export interface UsuarioDiscord {
  id: string;
  username: string;
  globalName: string | null;
  avatar: string | null;
}

export interface ParametrosComparar {
  base_id: string;
  encantamiento: number;
  calidad: number;
  cantidad: number;
}

/** Lo que el bot sabe pedirle a la API, siempre en nombre de quien usó el comando. */
export interface ClienteApi {
  buscarObjetos(texto: string): Promise<ObjetoCatalogo[]>;
  obtenerObjeto(baseId: string): Promise<ObjetoCatalogo>;
  comparar(parametros: ParametrosComparar): Promise<Comparacion[]>;
  saldoInicial(): Promise<SaldoInicial | null>;
  evolucion(): Promise<PuntoBalance[]>;
  reportes(desde?: string): Promise<Reportes>;
  registrarVenta(venta: NuevaVenta): Promise<Venta>;
  registrarGasto(gasto: NuevoGasto): Promise<Gasto>;
}

export interface Contexto {
  api: ClienteApi;
  ahora: () => Date;
}
