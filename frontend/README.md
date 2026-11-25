# Frontend: gestión de ventas del gremio

Aplicación web (React + TypeScript + Vite) con estilo **Bento Grid**, tema oscuro y claro, y todo en
español de México. Se publica en GitHub Pages y habla con la API del [backend](../backend/README.md).

## Pantallas

| Sección | Qué hace |
|---|---|
| **Panel** | Saldo del gremio y su evolución, resumen del periodo, impuestos y gastos, mejores oportunidades de venta, alertas y últimas ventas |
| **Comparador** | Para un objeto, en qué ciudad conviene vender y si rinde más como venta directa u orden de venta, con la antigüedad de cada precio |
| **Ventas** | Lista con filtros y totales; registrar, importar desde CSV, exportar a CSV o Excel y eliminar |
| **Gastos** | Lo mismo para los gastos del gremio |
| **Reportes** | Resultado, impuestos pagados (y qué % de lo vendido se fue en ellos), gastos por categoría y ganancia por objeto |
| **Alertas** | Objetos vigilados y las alertas que han saltado |

Quien tiene el rol de **administrador** registra, importa y elimina. Quien tiene el de **general** consulta y exporta.

## Desarrollo

Desde `frontend/`:

```bash
npm install
cp .env.example .env.local      # solo si tu API no está en http://localhost:8000
npm run dev                     # http://localhost:5173
```

El backend debe estar corriendo y su `GREMIO_CORS_ORIGENES` debe incluir `http://localhost:5173`.
Para entrar se usa el inicio de sesión con Discord de la API.

```bash
npm test            # pruebas (Vitest + Testing Library)
npm run typecheck   # tipos
npm run build       # construye en dist/
```

## Cómo está organizado

```
src/api/         cliente HTTP, tipos de la API y consultas (React Query)
src/sesion/      token de sesión y pantalla de entrada
src/ui/          sistema de diseño: bloques, cajón, avisos, marco, tema
src/componentes/ piezas con lógica: formularios, buscador de objetos, tarjetas, gráficas
src/paginas/     una por sección
src/util/        funciones puras: formato de plata y fechas, desglose, comparación
src/estilos/     tokens de color (oscuro y claro) y estilos
```

Notas de diseño que conviene saber:

- **El token de sesión** llega en la dirección como `#token=...`; la app lo guarda y limpia la barra al instante.
- **Las rutas usan `#`** (por ejemplo `#/ventas`) porque GitHub Pages no sabe redirigir rutas normales.
- **Las fechas** se muestran en la hora de quien mira; los días del balance usan la hora del juego (UTC).
- **El desglose del formulario de venta** es solo una vista previa; el cálculo que cuenta lo hace la API.

## Publicar en GitHub Pages

1. En el repositorio: **Settings → Pages → Source: GitHub Actions**.
2. **Settings → Secrets and variables → Actions → Variables → New repository variable**:
   `VITE_API_URL` = la dirección pública de tu API, con `https://` (por ejemplo, tu dominio de ngrok).
3. Haz push a `main`: el flujo `.github/workflows/frontend.yml` revisa, prueba, construye y publica.
4. En el `.env` del backend:

```
GREMIO_FRONTEND_URL=https://TUUSUARIO.github.io/NOMBRE-DEL-REPO/
GREMIO_CORS_ORIGENES=https://TUUSUARIO.github.io
```

   y agrega `https://TU-DOMINIO/api/auth/discord/callback` en **Redirects** del portal de Discord.
