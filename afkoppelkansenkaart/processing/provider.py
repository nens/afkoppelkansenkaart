from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from afkoppelkansenkaart.processing.height_estimation_algorithm import HeightEstimatorAlgorithm
from afkoppelkansenkaart.processing.parcels_to_postgis import Parcels2PostGISAlgorithm
from afkoppelkansenkaart.processing.inloop_to_postgis import Inloop2PostGISAlgorithm

class AfkoppelKansenKaartProvider(QgsProcessingProvider):
    """Loads the Processing Toolbox algorithms for 3Di"""

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(Parcels2PostGISAlgorithm())
        self.addAlgorithm(Inloop2PostGISAlgorithm())
        self.addAlgorithm(HeightEstimatorAlgorithm())
       
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
