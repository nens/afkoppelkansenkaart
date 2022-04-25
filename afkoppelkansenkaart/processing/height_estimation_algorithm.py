# -*- coding: utf-8 -*-

"""
/***************************************************************************
 HeightEstimator
                                 A QGIS plugin
 Calculate Height
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
__date__ = "2022-03-1"
__copyright__ = "(C) 2022 by Nelen en Schuurmans"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis import processing
from qgis.core import QgsProcessing
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm
from qgis.core import QgsProcessingException
from qgis.core import QgsProject
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsExpression
from qgis.core import QgsFeatureRequest
from ..database import execute_sql_query

class HeightEstimatorAlgorithm(OrderedProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT_DEM = "INPUT_DEM"
    INPUT_POL = "INPUT_POL"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_DEM, self.tr("Digital Elevation Model"))
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_POL, self.tr("Perceel polygon"), [QgsProcessing.TypeVectorPolygon] )
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
        success = False
        input_pol_source_layer = self.parameterAsVectorLayer(parameters, self.INPUT_POL, context)
        target_field_idx = input_pol_source_layer.fields().indexFromName('maaiveldhoogte')
        if target_field_idx == -1:
            feedback.reportError("Ongeldige percelenlaag: het veld 'maaiveldhoogte' ontbreekt", fatalError=True)
            return {self.OUTPUT: success}
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)

        if input_pol_source_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POL))
            
        if dem_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_DEM))
            
        self.parameterAsBool(
            parameters,
            self.OUTPUT,
            context,
        )
 
        if feedback.isCanceled():
            return {self.OUTPUT: success}
            
        #zonal statistics (the "fb" variant outputs a new layer)
        zonal_statistics_run = processing.run(
            "native:zonalstatisticsfb",
            {
                'INPUT': parameters[self.INPUT_POL],
                'INPUT_RASTER': parameters[self.INPUT_DEM],
                'RASTER_BAND': 1,
                'COLUMN_PREFIX': 'maaiveldhoogte_',
                'STATISTICS': [3],  # MEDIAN
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )

        zonal_statistics = context.getMapLayer(zonal_statistics_run['OUTPUT'])

        # for debugging: add the raw layer to the project tree
        # self.add_to_layer_tree_group(zonal_statistics)

        input_pol_source_layer.startEditing()
        for feature in zonal_statistics.getFeatures():

            if feedback.isCanceled():
                break

            # The id() function of PYQGIS does not need to match the attribute value 'ID' (seems to 
            # return index in current sorting): do an explicit join on 'ID'
            zonal_temp_id = feature.attribute('id')

            # find the parcels with the same ID
            expression = QgsExpression(f'id = {zonal_temp_id}')
            if expression.hasParserError():
                feedback.reportError(expression.parserErrorString())
                return {self.OUTPUT: success}

            request = QgsFeatureRequest(expression)
            
            duplicate = False
            for source_feature in input_pol_source_layer.getFeatures(request):
            
                if duplicate:
                    feedback.reportError(self.tr('Laag bevat percelen met dezelfde ID:') + f'{zonal_temp_id}')
                    input_pol_source_layer.rollBack()
                    return {self.OUTPUT: success}
                    
                # feedback.pushInfo(f"maaiveldhoogte van feature {source_feature.id()}-{source_feature.attribute('brk_lokaalid')} wordt nu {feature.attribute('maaiveldhoogte_median')} van {feature.id()}-{feature.attribute('brk_lokaalid')}")
                feedback.pushInfo(f"maaiveldhoogte van feature {source_feature.attribute('id')}-{source_feature.attribute('brk_lokaalid')} wordt nu {feature.attribute('maaiveldhoogte_median')} van {zonal_temp_id}-{feature.attribute('brk_lokaalid')}")
                if ( source_feature.attribute('id') != zonal_temp_id):
                    feedback.reportError(f"incorrecte ID: {source_feature.attribute('id')} ({type(source_feature.attribute('id'))}) vs {zonal_temp_id} ({type(zonal_temp_id)})")
                    input_pol_source_layer.rollBack()
                    return {self.OUTPUT: success}

                input_pol_source_layer.changeAttributeValue(
                    source_feature.id(),
                    target_field_idx,
                    feature.attribute('maaiveldhoogte_median')
                )
                duplicate = True

        if not input_pol_source_layer.commitChanges():
            feedback.pushInfo("Committen mislukt")
            for error_mes in input_pol_source_layer.commitErrors():
                feedback.pushInfo(error_mes)
            return {self.OUTPUT: success}

        if feedback.isCanceled():
            return {self.OUTPUT: success}
        
        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "heightestimator"

    def displayName(self):
        return self.tr("Hoogteligging")

    def group(self):
        return self.tr("Percelen verrijken")

    def groupId(self):
        return "Percelen verrijken"

    def shortHelpString(self):
        return self.tr("Bepaal de (mediane) hoogteligging van elk perceel op basis van de opgegeven DEM.")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return HeightEstimatorAlgorithm()

    @property
    def layer_group(self):
        root = QgsProject.instance().layerTreeRoot()
        _layer_group = root.findGroup('Afkoppelkansenkaart')
        if not _layer_group:
            _layer_group = root.insertGroup(0, 'Afkoppelkansenkaart')
        return _layer_group

    def add_to_layer_tree_group(self, layer):
        """
        Add a layer to the Afkoppelkansenkaart layer tree group
        """
        project = QgsProject.instance()
        project.addMapLayer(layer, addToLegend=False)
        self.layer_group.insertLayer(0, layer)