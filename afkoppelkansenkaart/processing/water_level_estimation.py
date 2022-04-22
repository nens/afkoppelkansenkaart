# -*- coding: utf-8 -*-

"""
/***************************************************************************
 WaterLevelEstimatorAlgorithm
                                 A QGIS plugin
 Calculate Height
                              -------------------
        begin                : 2022-04-22
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
__date__ = "2022-04-22"
__copyright__ = "(C) 2022 by Nelen en Schuurmans"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis import processing
from qgis.core import QgsProcessing
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication

class WaterLevelEstimatorAlgorithm(OrderedProcessingAlgorithm):

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
            QgsProcessingParameterRasterLayer(self.INPUT_DEM, self.tr("Grondwaterstand model"))
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
        input_pol_source = self.parameterAsSource(parameters, self.INPUT_POL, context)
        input_pol_source_layer = self.parameterAsVectorLayer(parameters, self.INPUT_POL, context)
        
        target_field_idx = input_pol_source.fields().indexFromName('ghg_tov_maaiveld')
        if target_field_idx == -1:
            feedback.reportError("Ongeldige percelenlaag: het veld 'ghg_tov_maaiveld' ontbreekt", fatalError=True)
            return {self.OUTPUT: success}

        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)

        if input_pol_source is None:
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
                'COLUMN_PREFIX': 'ghg_tov_maaiveld_',
                'STATISTICS': [3],  # MEDIAN
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )

        zonal_statistics = context.getMapLayer(zonal_statistics_run['OUTPUT'])
        input_pol_source_layer.startEditing()
        for feature in zonal_statistics.getFeatures():

            if feedback.isCanceled():
                break

            source_feature = input_pol_source_layer.getFeature(feature.id())
            feedback.pushInfo(f"ghg_tov_maaiveld van feature {source_feature.id()} wordt nu "
                              f"{feature.attribute('ghg_tov_maaiveld_median')}")
            input_pol_source_layer.changeAttributeValue(
                source_feature.id(),
                target_field_idx,
                feature.attribute('ghg_tov_maaiveld_median')
            )
        input_pol_source_layer.commitChanges()

        # processing.run("native:zonalstatistics", {
        #     'INPUT_VECTOR': parameters[self.INPUT_POL],
        #     'INPUT_RASTER': parameters[self.INPUT_DEM],
        #     'RASTER_BAND':1,
        #     'COLUMN_PREFIX':'test_ghg_maaiveld_',
        #     'STATISTICS':[3], #MEDIAN
        #     }, context=context, feedback=feedback, is_child_algorithm=True)

        # if feedback.isCanceled():
        #     return {self.OUTPUT: success}
        
        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "waterlevelestimator"

    def displayName(self):
        return self.tr("Gemiddelde hoogte grondwaterstand")

    def group(self):
        return self.tr("Percelen verrijken")

    def groupId(self):
        return "Percelen verrijken"

    def shortHelpString(self):
        return self.tr("Bepaal de (mediane) hoogte van de grondwaterstand van elk perceel op basis van de opgegeven DEM.")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return WaterLevelEstimatorAlgorithm()
