import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { useAvisos } from "../ui/Avisos";
import { guardarArchivo } from "../util/descargar";
import { useCliente } from "./ContextoApi";
import { ErrorApi, type Cliente, type Parametros } from "./cliente";
import type {
  Alerta, CategoriaGasto, CategoriaObjeto, Ciudad, Comparacion, Gasto, NuevaVenta, NuevoGasto,
  NuevoSeguimiento, ObjetoCatalogo, PuntoBalance, Reportes, ResultadoImportacion, SaldoInicial,
  Seguimiento, TipoVenta, Venta,
} from "./tipos";

export type FiltroVentas = { desde?: string; hasta?: string; ciudad?: Ciudad | ""; tipo?: TipoVenta | ""; base_id?: string };
export type FiltroGastos = { desde?: string; hasta?: string; categoria?: CategoriaGasto | "" };
export type Periodo = { desde?: string; hasta?: string };
export type ConsultaComparacion = { base_id: string; encantamiento: number; calidad: number; cantidad: number };

const noEncontrado = (error: unknown) => error instanceof ErrorApi && error.status === 404;

// ---------- Lecturas ----------

export function useVentas(filtro: FiltroVentas = {}) {
  const c = useCliente();
  return useQuery({ queryKey: ["ventas", filtro], queryFn: () => c.get<Venta[]>("/api/ventas", filtro) });
}

export function useGastos(filtro: FiltroGastos = {}) {
  const c = useCliente();
  return useQuery({ queryKey: ["gastos", filtro], queryFn: () => c.get<Gasto[]>("/api/gastos", filtro) });
}

export function useCatalogo(texto: string, categoria?: CategoriaObjeto | "") {
  const c = useCliente();
  const q = texto.trim();
  return useQuery({
    queryKey: ["catalogo", q, categoria ?? ""],
    queryFn: () => c.get<ObjetoCatalogo[]>("/api/catalogo", { q, categoria, limite: 12 }),
    enabled: q.length >= 2,
    staleTime: 5 * 60_000,
  });
}

export function useObjeto(baseId: string | null) {
  const c = useCliente();
  return useQuery({
    queryKey: ["objeto", baseId],
    queryFn: () => c.get<ObjetoCatalogo>(`/api/catalogo/${encodeURIComponent(baseId ?? "")}`),
    enabled: baseId !== null,
    staleTime: Infinity,
  });
}

/** Opciones de la consulta del comparador; se comparten con quien necesite varias a la vez. */
export function opcionesComparacion(c: Cliente, consulta: ConsultaComparacion) {
  return {
    queryKey: ["comparacion", consulta] as const,
    queryFn: () => c.get<Comparacion[]>("/api/mercado/comparar", consulta),
    staleTime: 60_000,
  };
}

export function useComparacion(consulta: ConsultaComparacion | null) {
  const c = useCliente();
  return useQuery({
    ...opcionesComparacion(c, consulta ?? { base_id: "", encantamiento: 0, calidad: 1, cantidad: 1 }),
    enabled: consulta !== null,
  });
}

/** El saldo inicial, o null si todavía no se configuró (la API responde 404). */
export function useSaldoInicial() {
  const c = useCliente();
  return useQuery({
    queryKey: ["saldo"],
    queryFn: async () => {
      try {
        return await c.get<SaldoInicial>("/api/balance/saldo-inicial");
      } catch (error) {
        if (noEncontrado(error)) return null;
        throw error;
      }
    },
  });
}

/** Saldo día a día; vacío si todavía no hay saldo inicial. */
export function useEvolucion() {
  const c = useCliente();
  return useQuery({
    queryKey: ["evolucion"],
    queryFn: async () => {
      try {
        return await c.get<PuntoBalance[]>("/api/balance/evolucion");
      } catch (error) {
        if (noEncontrado(error)) return [];
        throw error;
      }
    },
  });
}

export function useReportes(periodo: Periodo = {}) {
  const c = useCliente();
  return useQuery({ queryKey: ["reportes", periodo], queryFn: () => c.get<Reportes>("/api/reportes", periodo) });
}

export function useSeguimientos() {
  const c = useCliente();
  return useQuery({ queryKey: ["seguimientos"], queryFn: () => c.get<Seguimiento[]>("/api/seguimientos") });
}

export function useAlertas(limite = 50) {
  const c = useCliente();
  return useQuery({ queryKey: ["alertas", limite], queryFn: () => c.get<Alerta[]>("/api/alertas", { limite }) });
}

// ---------- Escrituras: al terminar, se vuelven a pedir los datos que cambian ----------

function useInvalidar() {
  const consultas = useQueryClient();
  return (...claves: string[]) => Promise.all(claves.map((clave) => consultas.invalidateQueries({ queryKey: [clave] })));
}

export function useRegistrarVenta() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (venta: NuevaVenta) => c.post<Venta>("/api/ventas", venta),
    onSuccess: () => invalidar("ventas", "reportes", "evolucion"),
  });
}

export function useEliminarVenta() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (id: number) => c.delete(`/api/ventas/${id}`),
    onSuccess: () => invalidar("ventas", "reportes", "evolucion"),
  });
}

export function useImportarVentas() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (archivo: File) => c.subir<ResultadoImportacion>("/api/ventas/importar", archivo),
    onSuccess: () => invalidar("ventas", "reportes", "evolucion"),
  });
}

export function useRegistrarGasto() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (gasto: NuevoGasto) => c.post<Gasto>("/api/gastos", gasto),
    onSuccess: () => invalidar("gastos", "reportes", "evolucion"),
  });
}

export function useEliminarGasto() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (id: number) => c.delete(`/api/gastos/${id}`),
    onSuccess: () => invalidar("gastos", "reportes", "evolucion"),
  });
}

export function useImportarGastos() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (archivo: File) => c.subir<ResultadoImportacion>("/api/gastos/importar", archivo),
    onSuccess: () => invalidar("gastos", "reportes", "evolucion"),
  });
}

export function useGuardarSaldoInicial() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (saldo: SaldoInicial) => c.put<SaldoInicial>("/api/balance/saldo-inicial", saldo),
    onSuccess: () => invalidar("saldo", "evolucion"),
  });
}

export function useCrearSeguimiento() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (seguimiento: NuevoSeguimiento) => c.post<Seguimiento>("/api/seguimientos", seguimiento),
    onSuccess: () => invalidar("seguimientos"),
  });
}

export function useEliminarSeguimiento() {
  const c = useCliente();
  const invalidar = useInvalidar();
  return useMutation({
    mutationFn: (id: number) => c.delete(`/api/seguimientos/${id}`),
    onSuccess: () => invalidar("seguimientos", "alertas"),
  });
}

// ---------- Descargas ----------

/** Devuelve una función que baja un archivo (CSV o Excel) y avisa si algo falla. */
export function useDescargar() {
  const c = useCliente();
  const { avisar } = useAvisos();
  return useCallback(
    async (ruta: string, params?: Parametros) => {
      try {
        const { archivo, nombre } = await c.descargar(ruta, params);
        guardarArchivo(archivo, nombre);
      } catch (error) {
        avisar(error instanceof Error ? error.message : "No se pudo descargar el archivo", "error");
      }
    },
    [c, avisar],
  );
}
