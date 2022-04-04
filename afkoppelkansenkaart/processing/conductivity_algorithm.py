# -*- coding: utf-8 -*-

"""
/***************************************************************************
 CalculateConductivityAlgorithm
                                 A QGIS plugin
 Calculates conductivity
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

class CalculateConductivityAlgorithm(OrderedProcessingAlgorithm):

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
            QgsProcessingParameterProviderConnection(self.INPUT_DB, self.tr("Connectienaam"), "postgres")
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_POL, self.tr("Perceel polygon"), [QgsProcessing.TypeVectorPolygon] )
        )

        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_DEM, self.tr("Bodemkaart"))
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

        execute_sql_script(connection_name, 'bofek_vertaaltabel', feedback)

        #zonal statistics (the "fb" variant outputs a new layer)
        zonal_statistics_run = processing.run(
            "native:zonalstatisticsfb",
            {
                'INPUT': parameters[self.INPUT_POL],
                'INPUT_RASTER': parameters[self.INPUT_DEM],
                'RASTER_BAND': 1,
                'COLUMN_PREFIX': 'pawn_code_',
                'STATISTICS': [9],  # MAJORITY
                'OUTPUT': 'TEMPORARY_OUTPUT'
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )

        # directly upload to postgis
        params = {
            'INPUT': zonal_statistics_run['OUTPUT'],
            'DATABASE': connection_name,
            'SCHEMA': 'public',
            'TABLENAME': 'bofek',
            'PRIMARY_KEY': 'id',
            'GEOMETRY_COLUMN': 'geom',
            'ENCODING': 'UTF-8',
            'OVERWRITE': True,
            'CREATEINDEX': True,
            'LOWERCASE_NAMES': True,
            'DROP_STRING_LENGTH': True,
            'FORCE_SINGLEPART': False
        }

        processing.run("qgis:importintopostgis", params, context=context, feedback=feedback)
        
        feedback.pushInfo(f"statistieken geimporteerd")

        execute_sql_script(connection_name, 'soil_type_and_hydraulic_conductivity', feedback)

        if feedback.isCanceled():
            return {self.OUTPUT: success}
        
        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "calculateconductivity"

    def displayName(self):
        return self.tr("Bepalen van doorlatendheid")

    def group(self):
        return self.tr("afkoppelkanskaart")

    def groupId(self):
        return "afkoppelkanskaart"

    def shortHelpString(self):

        return self.tr("Bepaal de doorlantendheid op basis van de opgegeven bodemkaart.")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return CalculateConductivityAlgorithm()
