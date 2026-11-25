import unicodedata


def normalizar_texto(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar lo que escribe una persona: "Báculo" == "baculo"."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c)
    )
    return sin_tildes.casefold()
