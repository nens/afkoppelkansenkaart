import os

PARCELS_WFS_URL = "pagingEnabled='true' restrictToRequestBBOX='1' srsname='EPSG:28992' typename='kadastralekaartv4:perceel' url='https://geodata.nationaalgeoregister.nl/kadastralekaart/wfs/v4_0' version='2.0.0'"
PARCEL_WFS_LAYER_NAME = "Kadastraal perceel (PDOK)"
PARCEL_POSTGIS_LAYER_NAME = "Perceel (PostGIS)"
MESSAGE_CATEGORY = 'Afkoppelkansenkaart'
SQL_DIR = os.path.join(os.path.dirname(__file__), 'sql')
BEWERKINGEN = [
    'Percelen toevoegen',
    'Stelseltype',
    'Verhardingspercentage',
    'Bebouwingspercentage',
    'Bodemberging',
    'Doorlatendheid',
    'Afstand tot bergingslocatie',
    'Af te koppelen oppervlak',
    'Gebiedstype wateroverlast',
    'Belasting oppervlaktewater',
    'Afstand tot RWZI',
    'Aantal keer verpompen'
]