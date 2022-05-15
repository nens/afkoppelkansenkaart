import os
from pathlib import Path
from typing import Union

from osgeo import ogr
from osgeo import osr
import psycopg2
import sqlite3
from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsAuthMethodConfig
from qgis.core import QgsApplication
from qgis.core import QgsDataSourceUri
from qgis.core import QgsVectorLayer

DRIVER = ogr.GetDriverByName('GPKG')
SQL_DIR = Path(__file__).parent / "sql"

MULTIPOLYGON = 'MULTIPOLYGON'

ogr.UseExceptions()
osr.UseExceptions()


class LayerDoesNotExistError(ValueError):
    pass


def get_postgis_layer(connection_name: str, pg_layer_name: str, qgis_layer_name: str = None,
                      geometry_column_name='geom', key_column_name=''):
    if not qgis_layer_name:
        qgis_layer_name = pg_layer_name
    uri = QgsDataSourceUri()
    params = get_pscycopg_connection_params(connection_name)
    uri.setConnection(
        aHost=params['host'],
        aPort=params['port'],
        aDatabase=params['dbname'],
        aUsername=params['user'],
        aPassword=params['password']
    )
    uri.setDataSource(
        aSchema='public',
        aTable=pg_layer_name,
        aGeometryColumn=geometry_column_name,
        aKeyColumn=key_column_name
    )

    layer = QgsVectorLayer(uri.uri(), qgis_layer_name, "postgres")
    return layer


def get_pscycopg_connection_params(connection_name: str):
    s = QSettings()
    s.beginGroup(f"PostgreSQL/connections/{connection_name}")
    result = {
        'host': s.value('host'),
        'port': s.value('port'),
        'user': s.value('username'),
        'password': s.value('password'),
        'dbname': s.value('database'),
    }
    if result['password'] == '':
        authcfg = s.value('authcfg')
        auth_mgr = QgsApplication.authManager()
        auth_method_config = QgsAuthMethodConfig()
        auth_mgr.loadAuthenticationConfig(authcfg, auth_method_config, True)
        config_map = auth_method_config.configMap()
        result['user'] = config_map['username']
        result['password'] = config_map['password']
    return result


def execute_sql_script(connection_name: str, sql_filename: str, feedback, parameters=None):
    sql_file_name = os.path.join(SQL_DIR, f'{sql_filename}.sql')
    with open(sql_file_name, 'r') as sql_file:
        sql = sql_file.read()
        if parameters is not None:
            sql = sql.format(**parameters)
            feedback.pushInfo(f"New query: {sql}")
        execute_sql_query(connection_name, sql, feedback)


def execute_sql_query(connection_name: str, query: str, feedback):
    try:
        conn = psycopg2.connect(**get_pscycopg_connection_params(connection_name))
    except psycopg2.OperationalError:
        feedback.reportError("Kan geen verbinding maken met de database", True)
        return

    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()


class Database:
    """
    Interact with geopackage file database
    """

    def __init__(self):
        self._epsg = None
        self._datasource = None
        self.srs = None
        self.gpkg_path = None
        self.datasource = None

    @property
    def epsg(self):
        return self._epsg

    @epsg.setter
    def epsg(self, value: int):
        self._epsg = value
        self.srs = osr.SpatialReference()
        self.srs.ImportFromEPSG(value)
        self._register_epsg()

    def create_datasource(self, filename: Union[str, Path]):
        """
        Create a geopackage file in the path specified by `filename`
        """
        path = Path(filename)
        if path.is_file():
            raise FileExistsError
        path.parent.mkdir(parents=True, exist_ok=True)
        self.gpkg_path = path.absolute()
        self.datasource = DRIVER.CreateDataSource(str(filename))

    def set_datasource(self, filename: Union[str, Path]):
        path = Path(filename)
        if path.is_file():
            self.gpkg_path = path.absolute()
            self.datasource = ogr.Open(str(filename), update=1)

    def execute_sql_file(self, basename):
        conn = sqlite3.connect(self.gpkg_path)
        cur = conn.cursor()

        sql_fn = SQL_DIR / str(basename + '.sql')

        with open(sql_fn) as file:
            sql = file.read()
            cur.executescript(sql)

    def _register_epsg(self):
        """
        Register self.srs in geopackage
        Only registers srs if no row of that id exists in gpkg_spatial_ref_sys
        """
        if self.srs.IsProjected():
            cstype = "PROJCS"
        elif self.srs.IsGeographic():
            cstype = "GEOGCS"
        else:
            raise ValueError(f"Invalid SRS: {self.srs}")

        sql = """SELECT * FROM gpkg_spatial_ref_sys WHERE srs_id = {}""".format(
            self.srs.GetAuthorityCode(cstype)
        )
        result_lyr = self.datasource.ExecuteSQL(sql)
        result_row_count = result_lyr.GetFeatureCount()
        self.datasource.ReleaseResultSet(result_lyr)
        if result_row_count == 0:
            sql = """
                    INSERT INTO gpkg_spatial_ref_sys (
                      srs_name,
                      srs_id,
                      organization,
                      organization_coordsys_id,
                      definition,
                      description
                    )
                    VALUES (
                        '{srs_name}',
                        {srs_id},
                        '{organization}',
                        {organization_coordsys_id},
                        '{definition}',
                        '{description}'
                    );
                    """.format(
                srs_name=self.srs.GetAttrValue(cstype),
                srs_id=self.srs.GetAuthorityCode(cstype),
                organization=self.srs.GetAuthorityName(cstype),
                organization_coordsys_id=self.srs.GetAuthorityCode(cstype),
                definition=self.srs.ExportToWkt(),
                description=self.srs.GetAttrValue(cstype),
            )
            self.datasource.ExecuteSQL(sql)

    def register_gpkg_layer(self, layer_name: str, column_name: str = 'geom', geometry_type: str = None, z=2, m=0):
        """Register tables as gpkg layer in geopackage admin tables. Will register layer_name as non-spatial tables if
        geometry_type is None"""

        sql = f"""DELETE FROM gpkg_contents WHERE table_name = '{layer_name}';"""
        self.datasource.ExecuteSQL(sql)

        sql = f"""DELETE FROM gpkg_geometry_columns WHERE table_name = '{layer_name}';"""
        self.datasource.ExecuteSQL(sql)

        data_type = "features" if geometry_type else "attributes"

        sql = f"""
                INSERT INTO gpkg_contents (
                    table_name,
                    data_type,
                    identifier,
                    description
                )
                VALUES ('{layer_name}', '{data_type}', '{layer_name}', '{layer_name}');
                """
        self.datasource.ExecuteSQL(sql)

        if geometry_type is not None:
            if self.srs.IsProjected():
                cstype = "PROJCS"
            elif self.srs.IsGeographic():
                cstype = "GEOGCS"
            else:
                raise ValueError("Invalid SRS")
            srs_id = self.srs.GetAuthorityCode(cstype)
            sql = f"""UPDATE gpkg_contents SET srs_id = {srs_id} WHERE table_name = '{layer_name}';"""
            self.datasource.ExecuteSQL(sql)

            sql = f"""
                    INSERT INTO gpkg_geometry_columns (table_name, column_name, geometry_type_name, srs_id, z, m)
                    VALUES ('{layer_name}','{column_name}','{geometry_type}',{srs_id},{z},{m});
                    """
            self.datasource.ExecuteSQL(sql)
            self.set_datasource(self.gpkg_path)

    def calculate_layer_extents(self, layer_name):
        lyr = self.datasource.GetLayerByName(layer_name)
        if lyr is None:
            raise LayerDoesNotExistError(layer_name)
        min_x, max_x, min_y, max_y = lyr.GetExtent()
        sql = f"""
                UPDATE  gpkg_contents 
                SET     min_x = {min_x}, 
                        max_x = {max_x}, 
                        min_y = {min_y}, 
                        max_y = {max_y}
                WHERE table_name = '{layer_name}'
                ;
                """
        self.datasource.ExecuteSQL(sql)

    def update_gpkg_ogr_contents(self, table_name):
        sql = f"""DELETE FROM gpkg_ogr_contents WHERE table_name = '{table_name}';"""
        self.datasource.ExecuteSQL(sql)
        sql = f"""
            INSERT INTO gpkg_ogr_contents (table_name, feature_count) 
            VALUES ('{table_name}', (SELECT count(*) FROM {table_name}));
        """
        self.datasource.ExecuteSQL(sql)


class MCADatabase(Database):
    """Database with tables and views to perform multi-criteria analysis"""

    PERCEEL = 'perceel'
    BUURT = 'buurt'
    WIJK = 'wijk'
    SCORE_ZOEKTABEL = 'score_zoektabel'
    HOOFDONDERDEEL = 'hoofdonderdeel'
    DOMEIN = 'domein'
    CRITERIUM = 'criterium'
    WEGING = 'weging'

    PERCEEL_CRITERIUMWAARDE = 'perceel_criteriumwaarde'
    PERCEEL_CRITERIUMSCORE = 'perceel_criteriumscore'
    PERCEEL_DOMEINSCORE = 'perceel_domeinscore'
    PERCEEL_HOOFDONDERDEELSCORE = 'perceel_hoofdonderdeelscore'
    PERCEEL_EINDSCORE = 'perceel_eindscore'
    BUURT_EINDSCORE = 'buurt_eindscore'
    WIJK_EINDSCORE = 'wijk_eindscore'

    TABLES_GEOMETRY_TYPES = {
        PERCEEL: MULTIPOLYGON,
        BUURT: MULTIPOLYGON,
        WIJK: MULTIPOLYGON,
        SCORE_ZOEKTABEL: None,
        HOOFDONDERDEEL: None,
        DOMEIN: None,
        CRITERIUM: None,
        WEGING: None
    }

    VIEWS_GEOMETRY_TYPES = {
        PERCEEL_CRITERIUMWAARDE: None,
        PERCEEL_CRITERIUMSCORE: None,
        PERCEEL_DOMEINSCORE: None,
        PERCEEL_HOOFDONDERDEELSCORE: None,
        PERCEEL_EINDSCORE: None,
        BUURT_EINDSCORE: MULTIPOLYGON,
        WIJK_EINDSCORE: MULTIPOLYGON
    }

    TABLES = list(TABLES_GEOMETRY_TYPES.keys())
    VIEWS = list(VIEWS_GEOMETRY_TYPES.keys())

    def __init__(self, result_view_name: str):
        super().__init__()
        self.result_view_name = result_view_name

    def create_schema(self):
        self.execute_sql_file('schema')
        self._register_layers()

    def create_perceel_criteriumwaarde_view(self):
        """Create a view containing, in each row one value for one (numbered) criterium of one parcel"""
        sql = f"DROP VIEW IF EXISTS perceel_criteriumwaarde;"
        self.datasource.ExecuteSQL(sql)
        select_clauses = []
        criterium_lyr = self.datasource.GetLayerByName('criterium')
        for criterium in criterium_lyr:
            select = f"SELECT   id AS perceel_id, " \
                     f"         {criterium.GetFID()} AS criterium_id," \
                     f"         CAST({criterium[0]} AS TEXT) AS waarde " \
                     f"FROM     perceel"
            select_clauses.append(select)
        select_str = " UNION ".join(select_clauses)
        sql = f"CREATE VIEW perceel_criteriumwaarde AS {select_str};"
        self.datasource.ExecuteSQL(sql)
        self.register_gpkg_layer(
            layer_name=self.PERCEEL_CRITERIUMWAARDE,
            geometry_type=self.VIEWS_GEOMETRY_TYPES[self.PERCEEL_CRITERIUMWAARDE]
        )
        self.update_gpkg_ogr_contents(self.PERCEEL_CRITERIUMWAARDE)

    def create_pivot_view(self):
        """Create a view containing one row for each perceel.
        Fields are all original perceel attributes plus all the scores as columns
        (i.e. 'pivoted' from the normalized score tables)"""

        select_clauses = []
        criterium_lyr = self.datasource.GetLayerByName('criterium')
        domein_lyr = self.datasource.GetLayerByName('domein')
        hoofdonderdeel_lyr = self.datasource.GetLayerByName('hoofdonderdeel')
        # Note: avg() is just a dummy aggregation method; all values that are aggregated here are the same
        for row in criterium_lyr:
            sql = f"""avg(case when criterium.criterium_id = {row.GetFID()} then criterium.score end) as {row[0]}"""
            select_clauses.append(sql)

        for row in domein_lyr:
            sql = f"""avg(case when domein.domein_id = {row.GetFID()} then domein.score end) as {row[0]}"""
            select_clauses.append(sql)

        for row in hoofdonderdeel_lyr:
            sql = f"""avg(case when hoofdonderdeel.hoofdonderdeel_id = {row.GetFID()} then hoofdonderdeel.score end) as {row[0]}"""
            select_clauses.append(sql)

        select_clauses_str = ', '.join(select_clauses)

        # sql = f"""DROP VIEW IF EXISTS {self.result_view_name};"""
        # self.datasource.ExecuteSQL(sql)

        sql = f"""
            CREATE VIEW IF NOT EXISTS {self.result_view_name} AS
            SELECT  perceel.*,
                    {select_clauses_str},
                    eind.score as eindscore
            FROM    perceel
            LEFT JOIN perceel_criteriumscore as criteriumscore
                ON  perceel.id = criteriumscore.perceel_id
            JOIN criterium 
                ON criteriumscore.criterium_id = criterium.id
            LEFT JOIN perceel_domeinscore as domeinscore
                ON  perceel.id = domeinscore.perceel_id
                    AND criterium.domein_id = domeinscore.domein_id
            JOIN domein
                ON domeinscore.domein_id = domein.id 
            LEFT JOIN perceel_hoofdonderdeelscore as hoofdonderdeelscore
                ON  perceel.id = hoofdonderdeelscore.perceel_id
                    AND domein.hoofdonderdeel_id = hoofdonderdeelscore.hoofdonderdeel_id
            LEFT JOIN perceel_eindscore AS eindscore
                ON  perceel.id = eindscore.perceel_id
            GROUP BY perceel.id
            ;
        """
        self.datasource.ExecuteSQL(sql)
        self.register_gpkg_layer(layer_name=self.result_view_name, geometry_type=MULTIPOLYGON)
        self.calculate_layer_extents(layer_name=self.result_view_name)
        self.update_gpkg_ogr_contents(table_name=self.result_view_name)

    def _register_layers(self):
        """Register all layers and views as geopackage layers"""
        for layer_name, geometry_type in {**self.TABLES_GEOMETRY_TYPES, **self.VIEWS_GEOMETRY_TYPES}.items():
            self.register_gpkg_layer(layer_name=layer_name, geometry_type=geometry_type)
            self.calculate_layer_extents(layer_name=layer_name)
        self._update_gpkg_ogr_contents_all_layers()

    def _update_gpkg_ogr_contents_all_layers(self):
        for layer_name in (self.TABLES + self.VIEWS):
            self.update_gpkg_ogr_contents(table_name=layer_name)

    def initialise(self):
        self.execute_sql_file('initialisation')
        self._update_gpkg_ogr_contents_all_layers()


class AfkoppelKansenKaartDatabase(MCADatabase):
    def __init__(self):
        super().__init__(result_view_name='afkoppelkansenkaart')
