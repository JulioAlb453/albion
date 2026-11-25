def clausula_where(condiciones: list[tuple[str, object | None]]) -> tuple[str, list[object]]:
    """Arma el WHERE solo con las condiciones cuyo valor no es None.

    Cada condición es `("columna = ?", valor)`. El texto SQL lo escribe el repositorio; los
    valores siempre van como parámetros, nunca dentro del texto.
    """
    usadas = [(sql, valor) for sql, valor in condiciones if valor is not None]
    if not usadas:
        return "", []
    return "WHERE " + " AND ".join(sql for sql, _ in usadas), [valor for _, valor in usadas]
