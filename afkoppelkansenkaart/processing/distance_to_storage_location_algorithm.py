# -*- coding: utf-8 -*-

"""
/***************************************************************************
 DistanceToStorageLocationAlgorithm
                                 A QGIS plugin
 Calculate distance to storage locations
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
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
from ..database import execute_sql_script

class DistanceToStorageLocationAlgorithm(OrderedProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT_DEM = "INPUT_DEM"
    INPUT_POL = "INPUT_POL"
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
            QgsProcessingParameterFeatureSource(self.INPUT_POL, self.tr("Berging locaties"), [QgsProcessing.TypeVectorPolygon] )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_DEM, self.tr("Digital Elevation Model"))
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
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        connection_name = self.parameterAsConnectionName(parameters, self.INPUT_DB, context)

        if input_pol_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POL))

        if connection_name is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_DB))

        if input_pol_source_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POL))
            
        if dem_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_DEM))
            
        self.parameterAsBool(
            parameters,
            self.OUTPUT,
            context,
        )

        target_field_idx = input_pol_source.fields().indexFromName('hoogte_median')
        if target_field_idx != -1:
                input_pol_source_layer.startEditing()
                input_pol_source_layer.deleteAttribute(target_field_idx)
                if input_pol_source_layer.commitChanges(): 
                    feedback.pushInfo('hoogte_medial attribuut verwijderd')
                else:
                    feedback.reportError("Verwijderen attribuut mislukt", fatalError=True)
                    return {self.OUTPUT: success}
                
        processing.run("native:zonalstatistics", { 
            'INPUT_VECTOR': parameters[self.INPUT_POL],
            'INPUT_RASTER': parameters[self.INPUT_DEM],
            'RASTER_BAND':1,
            'COLUMN_PREFIX':'hoogte_',
            'STATISTICS':[3], #MEDIAN
            }, context=context, feedback=feedback, is_child_algorithm=True)
        
        execute_sql_script(connection_name, 'distance_to_storage_location', feedback)
        
        feedback.pushInfo(f"Locaties bepaald")

        if feedback.isCanceled():
            return {self.OUTPUT: success}
        
        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "distancestorage"

    def displayName(self):
        return self.tr("Afstand tot potentiële bergingslocaties")

    def group(self):
        return self.tr("Percelen verrijken")

    def groupId(self):
        return "Percelen verrijken"

    def shortHelpString(self):
        return self.tr("Bepaal de afstand tot berginglocaties op basis van de opgegeven DEM.")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return DistanceToStorageLocationAlgorithm()
