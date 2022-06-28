# -*- coding: utf-8 -*-

"""
/***************************************************************************
 DistanceToRWZIAlgorithm
                                 A QGIS plugin
 Calculate distance to RWZI
                              -------------------
        begin                : 2022-04-20
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
__date__ = "2022-04-20"
__copyright__ = "(C) 2022 by Nelen en Schuurmans"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis import processing
from qgis.core import QgsProcessing
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
from ..database import execute_sql_script

class DistanceToRWZIAlgorithm(OrderedProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT_POL = "INPUT_POL"
    INPUT_DB = "INPUT_DB"

    REQUIRES_WFS_PARCELS_LAYER = False
    REQUIRES_POSTGIS_PARCELS_LAYER = True

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterProviderConnection(self.INPUT_DB, self.tr("Connectie naam"), "postgres")
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT_POL, self.tr("RWZI's"), [QgsProcessing.TypeVectorPoint] )
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
        input_pol = self.parameterAsVectorLayer(parameters, self.INPUT_POL, context)
        connection_name = self.parameterAsConnectionName(parameters, self.INPUT_DB, context)

        if input_pol is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POL))

        if connection_name is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_DB))

        self.parameterAsBool(
            parameters,
            self.OUTPUT,
            context,
        )

        # Do some checking on the layers coordinate reference system (CRS)
        if input_pol.crs().authid() != 'EPSG:28992':
            feedback.reportError(f'Input laag niet in EPSG:28992, maar in {input_pol.crs().authid()} ({input_pol.crs().description()})')
            # https://gis.stackexchange.com/questions/316002/pyqgis-reproject-layer
            # https://docs.qgis.org/3.22/en/docs/user_manual/processing_algs/qgis/vectorgeneral.html#reproject-layer
            return {self.OUTPUT: success}
        
        params = {
            'INPUT': parameters[self.INPUT_POL],
            'DATABASE': connection_name,
            'SCHEMA': 'public',
            'TABLENAME': 'rwzi',
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

        feedback.pushInfo(f"RWZI's geïmporteerd in PostGIS.")

        execute_sql_script(connection_name, 'distance_to_sewage_treatment_plant', feedback)
               
        feedback.pushInfo(f"Afstand to RWZI's bepaald.")

        if feedback.isCanceled():
            return {self.OUTPUT: success}
        
        success = True
        return {self.OUTPUT: success}

    def name(self):
        return "distancerwzi"

    def displayName(self):
        return self.tr("Afstand tot RWZI")

    def group(self):
        return self.tr("Percelen verrijken")

    def groupId(self):
        return "Percelen verrijken"

    def shortHelpString(self):
        return self.tr("Bepaal de afstand tot rioolwaterzuiveringsinstallaties.")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return DistanceToRWZIAlgorithm()
