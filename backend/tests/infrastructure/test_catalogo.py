import pytest

from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.mercado.infrastructure.catalogo_items_json import leer_catalogo
from src.mercado.infrastructure.sqlite_catalogo_objetos import SqliteCatalogoObjetos

ARMA, ARMADURA, ARTEFACTO = CategoriaObjeto.ARMA, CategoriaObjeto.ARMADURA, CategoriaObjeto.ARTEFACTO

ENCANTAMIENTOS = {"enchantment": [{"@enchantmentlevel": str(n)} for n in (1, 2, 3, 4)]}

# Forma del items.json original del volcado (ao-bin-dumps): objetos agrupados por tipo,
# con su categoría de mercado y sus atributos.
DATOS = {
    "items": {
        "shopcategories": {"shopcategory": []},
        "weapon": [
            {"@uniquename": "T4_MAIN_SWORD", "@shopcategory": "weapons", "@maxqualitylevel": "5", "enchantments": ENCANTAMIENTOS},
            {"@uniquename": "T4_2H_TOOL_AXE", "@shopcategory": "gathering", "@maxqualitylevel": "5"},
            {"@uniquename": "T4_MAIN_SWORD", "@shopcategory": "weapons", "@maxqualitylevel": "5"},  # repetida
        ],
        "equipmentitem": [
            {"@uniquename": "T4_CAPE", "@shopcategory": "capes", "@maxqualitylevel": "5", "enchantments": ENCANTAMIENTOS},
            {"@uniquename": "T4_ARMOR_PLATE_SET1", "@shopcategory": "armors", "@maxqualitylevel": "5", "enchantments": ENCANTAMIENTOS},
            {"@uniquename": "T4_BAG", "@shopcategory": "bags", "@maxqualitylevel": "5", "enchantments": ENCANTAMIENTOS},
        ],
        "mount": {"@uniquename": "T4_MOUNT_HORSE", "@shopcategory": "mounts", "@maxqualitylevel": "5"},
        "consumableitem": [
            {"@uniquename": "T4_MEAL_STEW", "@shopcategory": "consumables",
             "enchantments": {"enchantment": [{"@enchantmentlevel": "1"}, {"@enchantmentlevel": "2"}, {"@enchantmentlevel": "3"}]}},
        ],
        "consumablefrominventoryitem": [
            {"@uniquename": "T4_SKILLBOOK_STANDARD", "@shopcategory": "consumables", "@shopsubcategory1": "tomes"},
            {"@uniquename": "T4_SKIN_PRIVADA", "@shopcategory": "vanity", "@tradable": "false"},
        ],
        "simpleitem": [
            {"@uniquename": "T4_ORE", "@shopcategory": "crafting", "@enchantmentlevel": "0"},
            {"@uniquename": "T4_ORE_LEVEL2", "@shopcategory": "crafting", "@enchantmentlevel": "2"},
            {"@uniquename": "T4_ARTEFACT_2H_BOW_KEEPER", "@shopcategory": "artefacts"},
            {"@uniquename": "T4_OCULTO", "@shopcategory": "other", "@showinmarketplace": "false"},
            {"@uniquename": "T4_SIN_CATEGORIA"},
            {"@uniquename": "TREASURE_KNOWLEDGE_RARITY1", "@shopcategory": "other"},  # sin tier: no entra
        ],
        "furnitureitem": {"@uniquename": "T4_FURNITUREITEM_CHEST", "@shopcategory": "furniture"},
    }
}

NOMBRES = [
    {"UniqueName": "T4_MAIN_SWORD", "LocalizedNames": {"EN-US": "Adept's Broadsword", "ES-ES": "Espada ancha del iniciado"}},
    {"UniqueName": "T4_CAPE", "LocalizedNames": {"ES-ES": "Capa del iniciado"}},
    {"UniqueName": "T4_MOUNT_HORSE", "LocalizedNames": {"EN-US": "Adept's Riding Horse"}},
    {"UniqueName": "T4_ORE_LEVEL2@2", "LocalizedNames": {"ES-ES": "Mineral de titanio excepcional"}},
    {"UniqueName": "T4_BAG", "LocalizedNames": None},
]


def por_id(objetos):
    return {o.base_id: o for o in objetos}


class TestLeerCatalogo:
    def test_entra_todo_lo_que_se_vende_en_el_mercado_una_vez(self):
        assert sorted(por_id(leer_catalogo(DATOS, NOMBRES))) == sorted([
            "T4_MAIN_SWORD", "T4_2H_TOOL_AXE", "T4_CAPE", "T4_ARMOR_PLATE_SET1", "T4_BAG", "T4_MOUNT_HORSE",
            "T4_MEAL_STEW", "T4_SKILLBOOK_STANDARD", "T4_ORE", "T4_ORE_LEVEL2", "T4_ARTEFACT_2H_BOW_KEEPER",
            "T4_FURNITUREITEM_CHEST",
        ])

    def test_categoria_segun_el_mercado(self):
        o = por_id(leer_catalogo(DATOS, NOMBRES))
        assert [o[i].categoria.value for i in (
            "T4_MAIN_SWORD", "T4_2H_TOOL_AXE", "T4_CAPE", "T4_ARMOR_PLATE_SET1", "T4_BAG", "T4_MOUNT_HORSE",
            "T4_MEAL_STEW", "T4_SKILLBOOK_STANDARD", "T4_ORE", "T4_ARTEFACT_2H_BOW_KEEPER", "T4_FURNITUREITEM_CHEST",
        )] == [
            "arma", "recoleccion", "capa", "armadura", "bolsa", "montura",
            "consumible", "consumible", "recurso", "artefacto", "mobiliario",
        ]

    def test_calidad_y_encantamientos_salen_del_propio_objeto(self):
        o = por_id(leer_catalogo(DATOS, NOMBRES))
        rango = lambda i: (o[i].tiene_calidad, o[i].encantamiento_min, o[i].encantamiento_max)  # noqa: E731
        assert rango("T4_CAPE") == (True, 0, 4)
        assert rango("T4_MOUNT_HORSE") == (True, 0, 0)
        assert rango("T4_MEAL_STEW") == (False, 0, 3)
        assert rango("T4_SKILLBOOK_STANDARD") == (False, 0, 0)
        assert rango("T4_ARTEFACT_2H_BOW_KEEPER") == (False, 0, 0)
        # los recursos encantados son otro objeto con su encantamiento fijo: T4_ORE_LEVEL2@2
        assert rango("T4_ORE_LEVEL2") == (False, 2, 2)

    def test_nombre_en_espanol_luego_ingles_luego_el_identificador(self):
        o = por_id(leer_catalogo(DATOS, NOMBRES))
        assert o["T4_MAIN_SWORD"].nombre == "Espada ancha del iniciado"
        assert o["T4_MOUNT_HORSE"].nombre == "Adept's Riding Horse"
        assert o["T4_ORE_LEVEL2"].nombre == "Mineral de titanio excepcional"
        assert o["T4_BAG"].nombre == "T4_BAG"


class TestObjeto:
    def test_sin_datos_del_volcado_usa_lo_tipico_de_su_categoria(self):
        assert (Objeto("T4_MAIN_SWORD", "x", ARMA).tiene_calidad, Objeto("T4_MAIN_SWORD", "x", ARMA).encantamiento_max) == (True, 4)
        assert Objeto("T4_ARTEFACT_X", "x", ARTEFACTO).tiene_calidad is False
        assert Objeto("T4_ARTEFACT_X", "x", ARTEFACTO).encantamiento_max == 0


ITEMS_BUSQUEDA = [
    Objeto("T4_MAIN_SWORD", "Espada ancha del iniciado", ARMA),
    Objeto("T4_2H_ARCANESTAFF", "Báculo arcano del iniciado", ARMA),
    Objeto("T4_ARMOR_PLATE_SET1", "Armadura de soldado del iniciado", ARMADURA),
    Objeto("T4_ARTEFACT_2H_BOW_KEEPER", "Hueso tallado del iniciado", ARTEFACTO),
    Objeto("T4_MAIN_MACE", "Adept's Mace", ARMA),
    Objeto("T4_MAIN_AXE", "T4_MAIN_AXE", ARMA),
    Objeto("T4_ORE_LEVEL2", "Mineral de titanio excepcional", CategoriaObjeto.RECURSO, False, 2, 2),
]


class TestSqliteCatalogoObjetos:
    @pytest.fixture
    async def catalogo(self, db):
        repo = SqliteCatalogoObjetos(db)
        await repo.reemplazar(ITEMS_BUSQUEDA)
        return repo

    async def test_busca_sin_importar_mayusculas_ni_tildes(self, catalogo):
        for texto in ("espada", "ESPADA ancha", "baculo", "Báculo"):
            assert await catalogo.buscar(texto), texto
        assert [o.base_id for o in await catalogo.buscar("baculo")] == ["T4_2H_ARCANESTAFF"]

    async def test_busca_por_palabras_sueltas_en_cualquier_orden(self, catalogo):
        # se escribe en singular o salteado: "zapato de asesino" debe hallar "Zapatos de asesino"
        assert [o.base_id for o in await catalogo.buscar("armadura iniciado")] == ["T4_ARMOR_PLATE_SET1"]
        assert [o.base_id for o in await catalogo.buscar("iniciado  soldado")] == ["T4_ARMOR_PLATE_SET1"]
        assert [o.base_id for o in await catalogo.buscar("espad anch")] == ["T4_MAIN_SWORD"]

    async def test_todas_las_palabras_deben_aparecer(self, catalogo):
        assert await catalogo.buscar("espada soldado") == []

    async def test_filtra_por_categoria_y_limita(self, catalogo):
        assert [o.base_id for o in await catalogo.buscar("del iniciado", ARTEFACTO)] == ["T4_ARTEFACT_2H_BOW_KEEPER"]
        assert len(await catalogo.buscar("del iniciado", limite=2)) == 2

    async def test_los_comodines_de_sql_no_son_comodines(self, catalogo):
        # Como comodines, "esp%" y "espad_" encontrarían "Espada ancha del iniciado".
        assert await catalogo.buscar("esp%") == []
        assert await catalogo.buscar("espad_") == []

    async def test_agrupa_el_mismo_objeto_de_distintos_tiers(self, db):
        repo = SqliteCatalogoObjetos(db)
        await repo.reemplazar(
            [Objeto(f"T{t}_MAIN_SWORD", f"Espada {t}", ARMA) for t in (8, 4, 6)]
            + [Objeto("T4_MAIN_AXE", "Hacha", ARMA)]
        )
        assert [o.base_id for o in await repo.buscar("")] == [
            "T4_MAIN_AXE", "T4_MAIN_SWORD", "T6_MAIN_SWORD", "T8_MAIN_SWORD"
        ]

    async def test_get_by_base_id(self, catalogo):
        assert (await catalogo.get_by_base_id("T4_MAIN_MACE")).nombre == "Adept's Mace"
        assert await catalogo.get_by_base_id("T9_NADA") is None

    async def test_reemplazar_sustituye_todo_el_contenido(self, catalogo):
        await catalogo.reemplazar([Objeto("T5_MAIN_SPEAR", "Lanza", ARMA)])
        assert [o.base_id for o in await catalogo.buscar("")] == ["T5_MAIN_SPEAR"]

    async def test_guarda_calidad_y_rango_de_encantamiento(self, catalogo):
        mineral = await catalogo.get_by_base_id("T4_ORE_LEVEL2")
        assert (mineral.categoria, mineral.tiene_calidad, mineral.encantamiento_min, mineral.encantamiento_max) == (
            CategoriaObjeto.RECURSO, False, 2, 2
        )
        assert (await catalogo.get_by_base_id("T4_MAIN_SWORD")).encantamiento_max == 4
