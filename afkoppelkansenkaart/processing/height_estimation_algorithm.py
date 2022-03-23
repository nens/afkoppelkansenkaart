# -*- coding: utf-8 -*-

"""
/***************************************************************************
 HeightEstimator
                                 A QGIS plugin
 Calculate Height
                              -------------------
        begin                : 2021-01-27
        copyright            : (C) 2021 by Nelen en Schuurmans
        email                : emile.debadts@nelen-schuurmans.nl
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

from qgis import processing
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProviderConnectionException
from qgis.core import QgsProviderRegistry
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication

from typing import List

class HeightEstimatorAlgorithm(QgsProcessingAlgorithm):

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
        
        input_pol_source = self.parameterAsSource(
            parameters,
            self.INPUT_POL,
            context
        )

        dem_layer = self.parameterAsRasterLayer(
            parameters,
            self.INPUT_DEM,
            context
        )

        if input_pol_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POL))
            
        if dem_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_DEM))
            
        success_param = self.parameterAsBool(
            parameters,
            self.OUTPUT,
            context,
        )
        
        success = False

        if feedback.isCanceled():
            return {self.OUTPUT: success}
            
        #zonal statistics (in place, taken from DrainLevelAlgorithm)
        processing.run("native:zonalstatistics", { #TODO: fb postfix?
            'INPUT_VECTOR': parameters[self.INPUT_POL],
            'INPUT_RASTER': parameters[self.INPUT_DEM],
            'RASTER_BAND':1,
            'COLUMN_PREFIX':'hoogteligging_',
            'STATISTICS':[3], #MEDIAN
            }, context=context, feedback=feedback, is_child_algorithm=True)
            
        if feedback.isCanceled():
            return {self.OUTPUT: success}
        
        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "HeightEstimator"

    def displayName(self):
        return self.tr("Height estimator")

    def group(self):
        return self.tr("Afkoppelrendement")

    def groupId(self):
        return "afkoppelrendement"

    def shortHelpString(self):

        help_string = "Hoogtebepaling op basis van percelen"

        return self.tr(help_string)

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return HeightEstimatorAlgorithm()
