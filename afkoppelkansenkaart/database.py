from pathlib import Path
from typing import Union

import ogr
import osr
import sqlite3


DRIVER = ogr.GetDriverByName('GPKG')
SQL_DIR = Path(__file__).parent / "sql"

MULTIPOLYGON = 'MULTIPOLYGON'

ogr.UseExceptions()
osr.UseExceptions()


class LayerDoesNotExistError(ValueError):
    pass


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


class AfkoppelKansenKaartDatabase(Database):

    PERCEEL = 'perceel'
    BUURT = 'buurt'
    WIJK = 'wijk'
    SCORE_ZOEKTABEL = 'score_zoektabel'
    EINDSCORE_DEEL = 'eindscore_deel'
    DOMEIN = 'domein'
    CRITERIUM = 'criterium'
    WEGING = 'weging'

    PERCEEL_CRITERIUMSCORES = 'perceel_criteriumscores'

    TABLES_GEOMETRY_TYPES = {
        PERCEEL: MULTIPOLYGON,
        BUURT: MULTIPOLYGON,
        WIJK: MULTIPOLYGON,
        SCORE_ZOEKTABEL: None,
        EINDSCORE_DEEL: None,
        DOMEIN: None,
        CRITERIUM: None,
        WEGING: None
    }

    VIEWS_GEOMETRY_TYPES = {
        PERCEEL_CRITERIUMSCORES: MULTIPOLYGON
    }

    TABLES = TABLES_GEOMETRY_TYPES.keys()
    VIEWS = VIEWS_GEOMETRY_TYPES.keys()

    def create_schema(self):
        conn = sqlite3.connect(self.gpkg_path)
        cur = conn.cursor()

        sql_fn = SQL_DIR / 'schema.sql'

        with open(sql_fn) as file:
            sql = file.read()
            [cur.execute(statement) for statement in sql.split(';')]
        self._register_layers()

    def _register_layers(self):
        """Register all layers and views as geopackage layers"""
        for layer_name, geometry_type in {**self.TABLES_GEOMETRY_TYPES, **self.VIEWS_GEOMETRY_TYPES}.items():
            self.register_gpkg_layer(layer_name=layer_name, geometry_type=geometry_type)
            self.calculate_layer_extents(layer_name=layer_name)

