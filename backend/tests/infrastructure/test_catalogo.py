import pytest

from src.mercado.domain.entities.objeto import CategoriaObjeto, Objeto
from src.mercado.infrastructure.catalogo_items_json import categoria_de, leer_catalogo
from src.mercado.infrastructure.sqlite_catalogo_objetos import SqliteCatalogoObjetos

ARMA, ARMADURA, ARTEFACTO = CategoriaObjeto.ARMA, CategoriaObjeto.ARMADURA, CategoriaObjeto.ARTEFACTO


@pytest.mark.parametrize(
    "unique_name, categoria",
    [
        ("T4_MAIN_SWORD", ARMA),
        ("T6_2H_BOW", ARMA),
        ("T4_OFF_SHIELD", ARMA),
        ("T4_ARMOR_PLATE_SET1", ARMADURA),
        ("T4_HEAD_PLATE_SET1", ARMADURA),
        ("T4_SHOES_PLATE_SET1", ARMADURA),
        ("T4_ARTEFACT_2H_BOW_KEEPER", ARTEFACTO),
        ("T4_MAIN_SWORD@1", None),        # variante encantada: se guarda solo la base
        ("T4_2H_TOOL_AXE", None),         # herramienta de recolección, no un arma
        ("T4_DEBUG_ARMOR_HIDDEN", None),
        ("T4_BAG", None),
        ("UNIQUE_HIDEOUT", None),
        ("T9_MAIN_SWORD", None),
    ],
)
def test_categoria_de(unique_name, categoria):
    assert categoria_de(unique_name) is categoria


ITEMS = [
    {"UniqueName": "UNIQUE_HIDEOUT", "LocalizedNames": {"ES-ES": "Kit de escondites"}},
    {"UniqueName": "T4_MAIN_SWORD", "LocalizedNames": {"EN-US": "Adept's Broadsword", "ES-ES": "Espada ancha del iniciado"}},
    {"UniqueName": "T4_MAIN_SWORD@1", "LocalizedNames": {"ES-ES": "Espada ancha del iniciado"}},
    {"UniqueName": "T4_2H_ARCANESTAFF", "LocalizedNames": {"ES-ES": "Báculo arcano del iniciado"}},
    {"UniqueName": "T4_ARMOR_PLATE_SET1", "LocalizedNames": {"ES-ES": "Armadura de soldado del iniciado"}},
    {"UniqueName": "T4_ARTEFACT_2H_BOW_KEEPER", "LocalizedNames": {"ES-ES": "Hueso tallado del iniciado"}},
    {"UniqueName": "T4_2H_TOOL_AXE", "LocalizedNames": {"ES-ES": "Hacha del recolector"}},
    {"UniqueName": "T4_MAIN_MACE", "LocalizedNames": {"EN-US": "Adept's Mace"}},
    {"UniqueName": "T4_MAIN_AXE", "LocalizedNames": None},
    {"UniqueName": "T4_MAIN_SWORD", "LocalizedNames": {"ES-ES": "Repetida"}},
    {"LocalizedNames": {"ES-ES": "Sin identificador"}},
]


class TestLeerCatalogo:
    def test_se_queda_con_armas_armaduras_y_artefactos_sin_variantes(self):
        assert [o.base_id for o in leer_catalogo(ITEMS)] == [
            "T4_MAIN_SWORD", "T4_2H_ARCANESTAFF", "T4_ARMOR_PLATE_SET1",
            "T4_ARTEFACT_2H_BOW_KEEPER", "T4_MAIN_MACE", "T4_MAIN_AXE",
        ]

    def test_prefiere_el_nombre_en_espanol(self):
        sword = leer_catalogo(ITEMS)[0]
        assert sword == Objeto("T4_MAIN_SWORD", "Espada ancha del iniciado", ARMA)

    def test_sin_espanol_usa_ingles_y_sin_nombres_usa_el_identificador(self):
        por_id = {o.base_id: o.nombre for o in leer_catalogo(ITEMS)}
        assert por_id["T4_MAIN_MACE"] == "Adept's Mace"
        assert por_id["T4_MAIN_AXE"] == "T4_MAIN_AXE"

    def test_un_identificador_repetido_se_toma_una_sola_vez(self):
        assert [o.base_id for o in leer_catalogo(ITEMS)].count("T4_MAIN_SWORD") == 1


class TestSqliteCatalogoObjetos:
    @pytest.fixture
    async def catalogo(self, db):
        repo = SqliteCatalogoObjetos(db)
        await repo.reemplazar(leer_catalogo(ITEMS))
        return repo

    async def test_busca_sin_importar_mayusculas_ni_tildes(self, catalogo):
        for texto in ("espada", "ESPADA ancha", "baculo", "Báculo"):
            assert await catalogo.buscar(texto), texto
        assert [o.base_id for o in await catalogo.buscar("baculo")] == ["T4_2H_ARCANESTAFF"]

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
