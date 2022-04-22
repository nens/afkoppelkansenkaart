from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from afkoppelkansenkaart.processing.height_estimation_algorithm import HeightEstimatorAlgorithm
from afkoppelkansenkaart.processing.parcels_to_postgis import Parcels2PostGISAlgorithm
from afkoppelkansenkaart.processing.inloop_to_postgis import Inloop2PostGISAlgorithm
from afkoppelkansenkaart.processing.percentage_built_up_algorithm import PercentageCultivationAlgorithm
from afkoppelkansenkaart.processing.percentage_impervious_algorithm import PercentageConcretisationAlgorithm
from afkoppelkansenkaart.processing.potential_storage_locations_algorithm import PotentialStorageLocationAlgorithm
from afkoppelkansenkaart.processing.parcels_to_geopackage import Parcels2GeoPackageAlgorithm
from afkoppelkansenkaart.processing.distance_to_storage_location_algorithm import DistanceToStorageLocationAlgorithm
from afkoppelkansenkaart.processing.transfer_sewerage_type_algorithm import TransferSewerageTypeAlgorithm
from afkoppelkansenkaart.processing.conductivity_algorithm import CalculateConductivityAlgorithm
from afkoppelkansenkaart.processing.distance_to_rwzi import DistanceToRWZIAlgorithm
from afkoppelkansenkaart.processing.water_level_estimation import WaterLevelEstimatorAlgorithm

class AfkoppelKansenKaartProvider(QgsProcessingProvider):
    """Loads the Processing Toolbox algorithms"""

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(Parcels2PostGISAlgorithm(0))
        self.addAlgorithm(Inloop2PostGISAlgorithm(1))
        self.addAlgorithm(HeightEstimatorAlgorithm(4))
        self.addAlgorithm(PercentageCultivationAlgorithm(2))
        self.addAlgorithm(TransferSewerageTypeAlgorithm(8))
        self.addAlgorithm(PercentageConcretisationAlgorithm(3))
        self.addAlgorithm(Parcels2GeoPackageAlgorithm(20))
        self.addAlgorithm(PotentialStorageLocationAlgorithm(5))
        self.addAlgorithm(DistanceToStorageLocationAlgorithm(6))
        self.addAlgorithm(CalculateConductivityAlgorithm(5))
        self.addAlgorithm(DistanceToRWZIAlgorithm(9))
        self.addAlgorithm(WaterLevelEstimatorAlgorithm(10))
       
    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return "Afkoppelkansenkaart"

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr("Afkoppelkansenkaart")

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(":/plugins/afkoppelkansenkaart/icon.png")
