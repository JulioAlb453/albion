import pytest

from src.bootstrap.configuracion import Configuracion, ErrorConfiguracion

SECRETO = {"GREMIO_JWT_SECRET": "x" * 32}


def test_exige_un_secreto_largo():
    with pytest.raises(ErrorConfiguracion, match="GREMIO_JWT_SECRET"):
        Configuracion.desde_entorno({})
    with pytest.raises(ErrorConfiguracion, match="32"):
        Configuracion.desde_entorno({"GREMIO_JWT_SECRET": "corto"})


def test_valores_por_defecto():
    config = Configuracion.desde_entorno(SECRETO)
    assert config.ruta_db == "data/gremio.db"
    assert (config.token_horas, config.intervalo_alertas_minutos) == (12, 15)
    assert config.cors_origenes == () and config.discord_webhook_alertas == ""


def test_lee_todo_del_entorno():
    config = Configuracion.desde_entorno(
        SECRETO
        | {
            "GREMIO_DB": "otra.db",
            "GREMIO_TOKEN_HORAS": "6",
            "GREMIO_INTERVALO_ALERTAS_MINUTOS": "5",
            "GREMIO_CORS_ORIGENES": "https://a.github.io, https://b.github.io",
            "GREMIO_FRONTEND_URL": "https://a.github.io/gremio/",
            "GREMIO_API_URL": "https://api.ngrok.app",
            "GREMIO_DISCORD_CLIENT_ID": "cid",
            "GREMIO_DISCORD_CLIENT_SECRET": "csecret",
            "GREMIO_DISCORD_BOT_TOKEN": "bot",
            "GREMIO_DISCORD_GUILD_ID": "g",
            "GREMIO_DISCORD_ROL_ADMIN_ID": "ra",
            "GREMIO_DISCORD_ROL_GENERAL_ID": "rg",
            "GREMIO_DISCORD_WEBHOOK_ALERTAS": "https://discord.com/api/webhooks/1/x",
        }
    )
    assert config.ruta_db == "otra.db" and config.token_horas == 6
    assert config.intervalo_alertas_minutos == 5
    assert config.cors_origenes == ("https://a.github.io", "https://b.github.io")
    assert (config.frontend_url, config.api_publica_url) == ("https://a.github.io/gremio/", "https://api.ngrok.app")
    assert (config.discord_client_id, config.discord_rol_general_id) == ("cid", "rg")


def test_la_clave_del_bot_es_opcional_pero_si_existe_debe_ser_larga():
    assert Configuracion.desde_entorno(SECRETO).bot_clave == ""
    with pytest.raises(ErrorConfiguracion, match="GREMIO_BOT_CLAVE"):
        Configuracion.desde_entorno(SECRETO | {"GREMIO_BOT_CLAVE": "corta"})
    assert Configuracion.desde_entorno(SECRETO | {"GREMIO_BOT_CLAVE": "b" * 32}).bot_clave == "b" * 32


def test_las_copias_de_seguridad_tienen_valores_por_defecto_y_se_configuran():
    por_defecto = Configuracion.desde_entorno(SECRETO)
    assert (por_defecto.respaldos_dir, por_defecto.respaldos_conservar) == ("respaldos", 30)
    config = Configuracion.desde_entorno(SECRETO | {"GREMIO_RESPALDOS_DIR": "/app/respaldos", "GREMIO_RESPALDOS_CONSERVAR": "0"})
    assert (config.respaldos_dir, config.respaldos_conservar) == ("/app/respaldos", 0)  # 0 las apaga


@pytest.mark.parametrize("valor", ["-1", "abc"])
def test_cuantas_copias_conservar_debe_ser_un_numero_no_negativo(valor):
    with pytest.raises(ErrorConfiguracion, match="GREMIO_RESPALDOS_CONSERVAR"):
        Configuracion.desde_entorno(SECRETO | {"GREMIO_RESPALDOS_CONSERVAR": valor})


def test_un_numero_invalido_dice_cual_variable_falla():
    with pytest.raises(ErrorConfiguracion, match="GREMIO_TOKEN_HORAS"):
        Configuracion.desde_entorno(SECRETO | {"GREMIO_TOKEN_HORAS": "abc"})
