# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Parcels2GeoPackageAlgorithm
                                 A QGIS plugin
 Imports PostGIS layers into geopackage
                              -------------------
        begin                : 2022-03-01
        copyright            : (C) 2022 by Nelen en Schuurmans
        email                : leendert.vanwolfswinkel@nelen-schuurmans.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = "Nelen en Schuurmans"
__date__ = "2021-01-27"
__copyright__ = "(C) 2021 by Nelen en Schuurmans"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingOutputBoolean
from qgis.core import QgsVectorLayer
from qgis.core import QgsProcessingParameterFile
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import edit
from ..constants import *
from ..database import execute_sql_script, get_postgis_layer
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm

class Parcels2GeoPackageAlgorithm(OrderedProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT_FILE = "INPUT_FILE"
    INPUT_DB = "INPUT_DB"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        self.addParameter(
            QgsProcessingParameterProviderConnection(self.INPUT_DB, self.tr("Connectie naam"), "postgres")
        )

        self.addParameter(
            QgsProcessingParameterFile(self.INPUT_FILE, self.tr("GeoPackage"))
        )

        self.addOutput(
            QgsProcessingOutputBoolean(
                self.OUTPUT,
                self.tr('Success')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback.pushInfo(f"Start exporteren van geopackage") 

        connection_name = self.parameterAsConnectionName(
            parameters, self.INPUT_DB, context
        )

        file_name = self.parameterAsFile(
            parameters, self.INPUT_FILE, context
        )

        success = False

        # Create a new view containing the (exact) same attr as the geopackage
        execute_sql_script(connection_name, 'create_view_perceel', feedback)
    
        postgis_parcel_source_layer = get_postgis_layer(
            connection_name,
            'perceel',
            qgis_layer_name = "perceel (PostGIS View)", 
            key_column_name='id' # Views require a key column name when retrieving
        )

        feedback.pushInfo(f"View vanuit PostGis geladen met {postgis_parcel_source_layer.featureCount()} features")

        # Belangrijk is wel dat de bestaande laag 'perceel' in de gpkg niet wordt 
        # vervangen, maar geleegd en opnieuw gevuld met features uit de postgislaag
        # this rules out the possibility of using native:package, native:savefeatures, gdal:convertformat
        # https://gis.stackexchange.com/questions/285346/adding-layers-to-geopackage-using-pyqgis

        export_layer = QgsVectorLayer(file_name + "|layername=perceel", "Afkoppelkansenkaart")
        if not export_layer.isValid():
            feedback.pushInfo("Laag niet valide")
            return {self.OUTPUT: success}
        
        feedback.pushInfo(f"Laag vanuit GeoPackage geladen met {export_layer.featureCount()} features")
        
        # another option would be to use QgsDataProvider::truncate()
        # https://gis.stackexchange.com/questions/215530/deleting-all-features-of-a-vector-layer-in-pyqgis
        with edit(export_layer):
             listOfIds = [feat.id() for feat in export_layer.getFeatures()]
             export_layer.deleteFeatures( listOfIds )
        
        if export_layer.featureCount() is not 0:
             feedback.pushInfo(f"Features verwijderen mislukt")
             return {self.OUTPUT: success}

        feedback.pushInfo(f"{export_layer.featureCount()} features resterend")

        # now add the postgis features to the layer in geopackage
        export_layer.startEditing()
        feedback.pushInfo(f"Begin kopiëren van {postgis_parcel_source_layer.featureCount()} features")

        for feature in postgis_parcel_source_layer.getFeatures():
            if not export_layer.addFeature(feature):
                feedback.pushInfo(f"Features toevoegen mislukt")
        
        if not export_layer.commitChanges():
            feedback.pushInfo(f"Committen mislukt")
            for error_mes in export_layer.commitErrors():
                feedback.pushInfo(error_mes)
            return {self.OUTPUT: success}

        return {self.OUTPUT: True}

    def name(self):
        return "parceltogeopackage"

    def displayName(self):
        return self.tr("Percelen naar GeoPackage")

    def group(self):
        return self.tr("afkoppelkanskaart")

    def groupId(self):
        return "afkoppelkanskaart"

    def shortHelpString(self):
        return self.tr("Importeren van percelenlaag in GeoPackage (laag Perceel)")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return Parcels2GeoPackageAlgorithm()
