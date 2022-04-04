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
from qgis.core import QgsVectorFileWriter
from qgis.core import QgsVectorLayer
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsFeature
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProject
from qgis.core import edit
from ..constants import *
from ..database import get_postgis_layer
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
        feedback.pushInfo(f"Start algo")

        connection_name = self.parameterAsConnectionName(
            parameters, self.INPUT_DB, context
        )

        file_name = self.parameterAsFile(
            parameters, self.INPUT_FILE, context
        )

        success = False
    
        postgis_parcel_source_layer = get_postgis_layer(
            connection_name,
            'kadastraal_perceel_subdivided',
            qgis_layer_name = PARCEL_POSTGIS_LAYER_NAME
        )

        # Belangrijk is wel dat de bestaande laag 'perceel' in de gpkg niet wordt 
        # vervangen, maar geleegd en opnieuw gevuld met features uit de postgislaag
        # this rules out the possibility of using native:package, native:savefeatures, gdal:convertformat
        # https://gis.stackexchange.com/questions/285346/adding-layers-to-geopackage-using-pyqgis

        layer = QgsVectorLayer(file_name + "|layername=perceel", "Afkoppelkansenkaart")
        if not layer.isValid():
            feedback.pushInfo("Laag niet valide")
            return {self.OUTPUT: success}
        
        feedback.pushInfo(f"Laag vanuit GeoPackage geladen met {layer.featureCount()} features")
        
        # another option would be to use QgsDataProvider::truncate()
        # https://gis.stackexchange.com/questions/215530/deleting-all-features-of-a-vector-layer-in-pyqgis
        with edit(layer):
            listOfIds = [feat.id() for feat in layer.getFeatures()]
            layer.deleteFeatures( listOfIds )
        
        if layer.featureCount() is not 0:
            feedback.pushInfo(f"Features verwijderen mislukt")
            return {self.OUTPUT: success}

        feedback.pushInfo(f"{layer.featureCount()} features resterend")

        # now add the postgis features to the layer in geopackage
        
        # processing.run("qgis:package", { 
        #     'LAYERS': [postgis_parcel_source_layer],
        #     'OVERWRITE': False, #layers will be appended
        #     'SAVE_STYLES':1,
        #     'OUTPUT':file_name,
        #     }, context=context, feedback=feedback, is_child_algorithm=True)
        
        # iterate over the attributes in the geopackage and check whether these are available in 
        # postgis layer

        gpk_field_names = layer.fields().names()
        postgis_field_names = postgis_parcel_source_layer.fields().names()

        # lists of attributes in both layers
        # union_field_names = [attr for attr in gpk_field_names if attr in postgis_field_names]
        # feedback.pushInfo('both')
        # feedback.pushInfo(",".join(union_field_names))
        
        # layer.startEditing()
        # feedback.pushInfo(f"Begin kopiëren van {postgis_parcel_source_layer.featureCount()} features")

        # 
        # postgis_field_names = postgis_parcel_source_layer.fields().names()
        # # return attributes in postgis, but not in package
        # diff_attributes = list(set(postgis_field_names) - set(gpk_field_names))
        # # these attributes indices are not present in the package
        # indices_to_drop = [postgis_field_names.index(i) for i in diff_attributes]
        # feedback.pushInfo(",".join([str(int) for int in indices_to_drop]))

        for feature in postgis_parcel_source_layer.getFeatures():
             # note that the geopackage layer might not contain all fields from postgis
             # so simply using addFeature will fail, remove unused attributes
             truncated_feature = QgsFeature(feature)
             #truncated_feature.deleteAttributes(indices_to_drop)
            
        #     if not layer.addFeature(truncated_feature):
        #         feedback.pushInfo(f"Features toevoegen mislukt")
        #         return {self.OUTPUT: success}

        # if not layer.commitChanges():
        #     feedback.pushInfo(f"Committen mislukt")
        #     for error_mes in layer.commitErrors():
        #         feedback.pushInfo(error_mes)
        #     return {self.OUTPUT: success}

        # # TODO: would we also like to add fields/attributes that are in PostGIS, but not in 
        # # geopackage? Currently not.
        # options = QgsVectorFileWriter.SaveVectorOptions()
        # options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
        # #options.layerName = "_".join(postgis_parcel_source_layer.name().split(' '))
        # _writer = QgsVectorFileWriter.write(postgis_parcel_source_layer, file_name, options)
        # if _writer:
        #     print(postgis_parcel_source_layer.name(), _writer)

        # look at https://gis.stackexchange.com/questions/109078/how-to-delete-column-field-in-pyqgis


        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "parceltogeopackage"

    def displayName(self):
        return self.tr("Percelen naar GeoPackage")

    def group(self):
        return self.tr("afkoppelkanskaart")

    def groupId(self):
        return "afkoppelkanskaart"

    def shortHelpString(self):
        return self.tr("Importeren van percelenlaag in GeoPackage")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return Parcels2GeoPackageAlgorithm()
    
    def add_to_layer_tree_group(self, layer):
        """
        Add a layer to the Afkoppelkansenkaart layer tree group
        """
        project = QgsProject.instance()
        project.addMapLayer(layer, addToLegend=False)
        self.layer_group.insertLayer(0, layer)

    @property
    def layer_group(self):
        root = QgsProject.instance().layerTreeRoot()
        _layer_group = root.findGroup('Afkoppelkansenkaart')
        if not _layer_group:
            _layer_group = root.insertGroup(0, 'Afkoppelkansenkaart')
        return _layer_group