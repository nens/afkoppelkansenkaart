from afkoppelkansenkaart.database import *

TEST_DB_PATH = SQL_DIR = Path(__file__).parent / 'test.gpkg'


def test_create_datasource():
    try:
        TEST_DB_PATH.unlink()  # missing_ok available in Python >= 3.8
    except FileNotFoundError:
        pass
    db = AfkoppelKansenKaartDatabase()
    db.create_datasource(TEST_DB_PATH)
    db.epsg = 28992
    db.create_schema()
    ogr_db = ogr.Open(str(TEST_DB_PATH))
    assert ogr_db.GetLayerByName(db.PERCEEL_CRITERIUMSCORES) is not None


test_create_datasource()
