from afkoppelkansenkaart.database import *

TEST_DB_PATH = SQL_DIR = Path(__file__).parent / 'test.gpkg'
NR_CRITERIA = 11


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
    assert ogr_db.GetLayerCount() == len(db.VIEWS) + len(db.TABLES)
    assert ogr_db.GetLayerByName(db.PERCEEL_EINDSCORE) is not None
    return db


def test_initialise(db):
    db.initialise()
    ogr_db = ogr.Open(str(TEST_DB_PATH))
    criterium_lyr = ogr_db.GetLayerByName(db.CRITERIUM)
    assert criterium_lyr.GetFeatureCount() == NR_CRITERIA
    return db


def test_create_pivot_view(db):
    db.create_pivot_view()
    ogr_db = ogr.Open(str(TEST_DB_PATH))
    assert ogr_db.GetLayerByName(db.PIVOT_VIEW) is not None
    return db

db = test_create_datasource()
db = test_initialise(db)
db = test_create_pivot_view(db)
