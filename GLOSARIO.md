# Glosario del dominio

Términos tal como los usa el código. Si un término cambia de significado, se cambia aquí primero.

## Mercado

| Término | Significado | En el código |
|---|---|---|
| **Objeto** | Entrada del catálogo del juego: tipo de arma, armadura o artefacto, con su nombre en español. No tiene encantamiento ni calidad. | `mercado/.../objeto.py` → `Objeto` |
| **Referencia de objeto** | Un objeto concreto que se compra y se vende: tipo, encantamiento y calidad. | `ObjetoRef` |
| **`base_id`** | Identificador de Albion sin encantamiento: `T6_MAIN_SWORD`. | `ObjetoRef.base_id` |
| **`api_id`** | Identificador que espera la API: `T6_MAIN_SWORD@2`. | `ObjetoRef.api_id` |
| **Tier** | Nivel del objeto, de 1 a 8. Es el dígito tras la `T`. | `ObjetoRef.tier` |
| **Encantamiento** | De 0 a 4. En notación de jugador va tras el punto: `T6.2`. | `ObjetoRef.encantamiento` |
| **Calidad** | Normal, Buena, Notable, Sobresaliente, Obra maestra (1–5, igual que la API). Los artefactos no tienen calidad. | `Calidad` |
| **Ciudad** | Mercado del servidor Americas, incluido el Black Market. | `Ciudad` |
| **Ciudad del gremio** | Ciudad donde el gremio tiene isla: Fort Sterling, Lymhurst y Caerleon. | `CIUDADES_GREMIO` |
| **Ciudad principal** | Fort Sterling. Es la referencia por defecto de las alertas. | `CIUDAD_PRINCIPAL` |
| **Black Market** | Mercado de Caerleon que solo tiene órdenes de compra. Ahí solo se vende directo. | `Ciudad.admite_orden_venta` |
| **Precio de mercado** | Foto de las órdenes de un objeto en una ciudad, tal como la reportan los jugadores. Un precio 0 significa que no hay dato. | `PrecioMercado` |
| **Venta mínima** | La orden de venta más barata publicada (`sell_price_min`). | `PrecioMercado.venta_minima` |
| **Compra máxima** | La orden de compra más alta publicada (`buy_price_max`). | `PrecioMercado.compra_maxima` |
| **Dato confiable** | Precio con 6 h de antigüedad o menos. Los datos viejos se muestran al final de la lista y nunca disparan alertas. | `OpcionVenta.confiable`, `ANTIGUEDAD_MAXIMA` |

## Venta e impuestos

| Término | Significado | En el código |
|---|---|---|
| **Venta directa** | Vender a la compra máxima. Es inmediata y solo paga impuesto. | `TipoVenta.DIRECTA` |
| **Orden de venta** | Publicar el objeto y esperar comprador. Paga impuesto y tarifa de publicación. | `TipoVenta.ORDEN` |
| **Impuesto de venta** | 4 % del bruto con premium (8 % sin premium). Se cobra al venderse el objeto. | `TasasMercado.impuesto_venta` |
| **Tarifa de publicación** | *Setup fee*: 2.5 % del bruto, cobrado al publicar la orden. **No se devuelve.** | `TasasMercado.tarifa_publicacion` |
| **Tarifa extra** | Tarifa pagada de nuevo al reajustar el precio de una orden ya publicada. | `tarifa_extra` |
| **Bruto** | Precio unitario × cantidad. | `DesgloseVenta.bruto` |
| **Cargos** | Impuesto más tarifa de publicación. | `DesgloseVenta.total_cargos` |
| **Neto** | Bruto menos cargos: la plata que de verdad recibe el gremio. | `DesgloseVenta.neto` |
| **Desglose** | Bruto, impuesto, tarifa y neto de una venta. Siempre cuadra: neto = bruto − cargos. | `DesgloseVenta` |
| **Opción de venta** | Una forma posible de vender: una ciudad y un tipo de venta, con su neto. | `OpcionVenta` |
| **Comparación por ciudad** | Venta directa contra orden en una misma ciudad, con la diferencia neta entre ambas. | `ComparacionCiudad` |

## Finanzas del gremio

| Término | Significado | En el código |
|---|---|---|
| **Venta** | Venta registrada de un objeto. Guarda su desglose. | `Venta` |
| **Gasto** | Salida de plata, con categoría: compra de equipo, reparaciones, reequipamiento de builds, ingredientes para comida u otros (este último exige descripción). | `Gasto`, `CategoriaGasto` |
| **Reequipamiento** | *Regear*: reponer el equipo que los miembros pierden en combate. | `CategoriaGasto.REEQUIPAMIENTO_BUILDS` |
| **Saldo inicial** | Plata del gremio el día en que empieza el registro (120 M). Los movimientos anteriores ya están contados en él. | `SaldoInicial` |
| **Punto de balance** | Ingresos netos, gastos y saldo al cierre de un día. | `PuntoBalance` |

## Alertas y usuarios

| Término | Significado | En el código |
|---|---|---|
| **Seguimiento** | Objeto vigilado, con al menos un criterio: porcentaje mínimo sobre la ciudad de referencia o neto unitario mínimo. | `Seguimiento` |
| **Alerta** | Aviso de que un seguimiento cumplió un criterio con un dato confiable. | `Alerta` |
| **Tiempo de espera** | Mínimo entre dos alertas del mismo seguimiento: 2 h. | `ESPERA_ENTRE_ALERTAS` |
| **Admin** | Registra ventas y gastos y configura alertas. | `Rol.ADMIN` |
| **General** | Solo consulta y exporta. | `Rol.GENERAL` |
| **Actor** | Usuario que ejecuta una operación. Toda operación que escribe lo recibe y exige que sea admin. | `exigir_admin` |

## Aplicación

| Término | Significado | En el código |
|---|---|---|
| **Caso de uso** | Una operación del sistema (registrar una venta, comparar precios…). Una clase por operación, con un método `ejecutar`. | `*/application/*_use_case.py` |
| **Hora UTC** | La hora del juego. Una fecha sin zona se toma como UTC y toda fecha se guarda en UTC. | `a_utc` |
| **Importación** | Carga de varias filas a la vez. Es todo o nada: si una fila es inválida no se guarda ninguna y se informan todas las malas con su número. | `importar`, `ResultadoImportacion` |
| **Actualizar precios** | Traer de la API los precios de un lote de objetos y reemplazar los guardados. | `ActualizarPrecios` |
| **Revisión de alertas** | Tarea periódica: actualiza los precios de los seguimientos con una sola consulta y avisa de los que cumplen su criterio. | `RevisarAlertas` |
| **Ganancia por objeto** | Neto de las ventas de un objeto concreto. No resta costos, porque el gremio no registra cuánto costó cada objeto. | `GananciaObjeto` |
| **Resultado** | Ventas netas menos gastos de un periodo. | `Reportes.resultado` |

## Infraestructura

| Término | Significado | En el código |
|---|---|---|
| **Sesión** | Una operación sobre la base de datos. Hay una sola conexión y un candado: una sesión a la vez, y lo que se hace dentro se confirma junto o se descarta junto. No se anidan. | `Database.sesion()` |
| **Migración** | Una versión del esquema de la base. Se aplican en orden al abrirla y nunca se edita una ya publicada: se agrega otra. La versión queda en `user_version`. | `MIGRACIONES` |
| **Caché de precios** | Último precio traído de la API por objeto, calidad y ciudad. Un precio nuevo reemplaza al anterior. | `precios_mercado` |
| **Catálogo** | Armas, armaduras y artefactos de crafteo del juego, con su nombre en español. Se carga con `scripts/importar_catalogo.py` y no incluye variantes encantadas ni herramientas de recolección. | `SqliteCatalogoObjetos` |
| **Sin datos** | La API marca con la fecha `0001-01-01` un precio que nadie ha reportado. En el dominio es `None`. | `_fecha` |
| **Servicio externo no disponible** | La API de Albion o Discord no respondió bien. No es un error de la petición: la capa HTTP lo traducirá a 502. | `ServicioExternoNoDisponible` |
