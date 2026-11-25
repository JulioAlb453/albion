import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PuntoBalance } from "../api/tipos";
import { Vacio } from "../ui/Bloque";
import { diaCorto, plataCompleta, plataCorta } from "../util/formato";

const EJE = { fill: "var(--texto-3)", fontSize: 12 };
const TOOLTIP = {
  contentStyle: {
    background: "var(--superficie-3)", border: "1px solid var(--borde-fuerte)",
    borderRadius: 12, color: "var(--texto)", fontSize: 13,
  },
  itemStyle: { color: "var(--texto)" },
  labelStyle: { color: "var(--texto-2)" },
};

/** Saldo del gremio día a día. */
export function GraficaBalance({ puntos, llena }: { puntos: PuntoBalance[]; llena?: boolean }) {
  if (puntos.length === 0) return <Vacio titulo="Todavía no hay movimientos" />;
  const datos = puntos.map((p) => ({ ...p, etiqueta: diaCorto(p.fecha) }));
  const primero = puntos[0]!;
  const ultimo = puntos[puntos.length - 1]!;
  return (
    <div
      className={llena ? "grafica grafica--llena" : "grafica"}
      role="img"
      aria-label={`Saldo del gremio de ${diaCorto(primero.fecha)} a ${diaCorto(ultimo.fecha)}: de ${plataCorta(primero.saldo)} a ${plataCorta(ultimo.saldo)}`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={datos} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="relleno-saldo" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" style={{ stopColor: "var(--acento)", stopOpacity: 0.35 }} />
              <stop offset="100%" style={{ stopColor: "var(--acento)", stopOpacity: 0 }} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--borde)" vertical={false} />
          <XAxis dataKey="etiqueta" tick={EJE} tickLine={false} axisLine={false} minTickGap={28} />
          <YAxis tick={EJE} tickLine={false} axisLine={false} width={60} tickFormatter={plataCorta} domain={["auto", "auto"]} />
          <Tooltip {...TOOLTIP} formatter={(valor) => [plataCompleta(Number(valor)), "Saldo"]} />
          <Area
            type="monotone" dataKey="saldo" stroke="var(--acento)" strokeWidth={2.5}
            fill="url(#relleno-saldo)" dot={puntos.length < 4} activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Barras horizontales: lo que dejó cada objeto, de mayor a menor. */
export function GraficaBarras({ datos }: { datos: DatoDona[] }) {
  if (datos.length === 0) return null;
  return (
    <div
      className="grafica"
      style={{ height: 36 + datos.length * 40 }}
      role="img"
      aria-label={`Ganancia por objeto: ${datos.map((d) => `${d.nombre} ${plataCorta(d.valor)}`).join(", ")}`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={datos} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--borde)" horizontal={false} />
          <XAxis type="number" tick={EJE} tickLine={false} axisLine={false} tickFormatter={plataCorta} />
          <YAxis
            type="category" dataKey="nombre" width={190} tick={EJE} tickLine={false} axisLine={false}
            tickFormatter={(nombre: string) => (nombre.length > 28 ? `${nombre.slice(0, 27)}…` : nombre)}
          />
          <Tooltip {...TOOLTIP} cursor={{ fill: "var(--superficie-3)", opacity: 0.4 }} formatter={(valor) => [plataCompleta(Number(valor)), "Neto"]} />
          <Bar dataKey="valor" fill="var(--acento)" radius={[0, 8, 8, 0]} barSize={20} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export interface DatoDona {
  nombre: string;
  valor: number;
}

/** Reparto de un total entre categorías. La leyenda es una lista, así el color no es lo único que informa. */
export function GraficaDona({ datos }: { datos: DatoDona[] }) {
  const total = datos.reduce((suma, d) => suma + d.valor, 0);
  if (total === 0) return <Vacio titulo="Sin datos en este periodo" />;
  const color = (indice: number) => `var(--c${(indice % 6) + 1})`;
  return (
    <div className="dona">
      <div className="dona__grafica" role="img" aria-label={`Reparto de ${plataCorta(total)}: ${datos.map((d) => `${d.nombre} ${plataCorta(d.valor)}`).join(", ")}`}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={datos} dataKey="valor" nameKey="nombre" innerRadius="62%" outerRadius="94%" paddingAngle={2} stroke="none">
              {datos.map((dato, indice) => (
                <Cell key={dato.nombre} fill={color(indice)} />
              ))}
            </Pie>
            <Tooltip {...TOOLTIP} formatter={(valor) => plataCompleta(Number(valor))} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="lista dona__leyenda">
        {datos.map((dato, indice) => (
          <li key={dato.nombre} className="lista__fila">
            <span className="punto" style={{ background: color(indice) }} aria-hidden="true" />
            <span className="lista__principal">{dato.nombre}</span>
            <span className="num" title={plataCompleta(dato.valor)}>{plataCorta(dato.valor)}</span>
            <span className="num texto-3">{Math.round((dato.valor / total) * 100)} %</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
