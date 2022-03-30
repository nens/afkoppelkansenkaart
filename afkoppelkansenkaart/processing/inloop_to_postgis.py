# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Inloop2PostGISAlgorithm
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
from qgis.core import QgsProcessingFeatureSourceDefinition
from qgis.core import QgsProcessingParameterMapLayer
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm
from ..constants import *

class Inloop2PostGISAlgorithm(OrderedProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT_POL = "INPUT_POL"
    INPUT_DB = "INPUT_DB"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        self.addParameter(
            QgsProcessingParameterMapLayer(self.INPUT_POL, self.tr("BGT Inlooptabel polygon"))
        )

        self.addParameter(
            QgsProcessingParameterProviderConnection(self.INPUT_DB, self.tr("Connectie naam"), "postgres")
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

        input_pol_source = self.parameterAsLayer(
            parameters,
            self.INPUT_POL,
            context
        )

        success = False
    
        if input_pol_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POL))

        feedback.pushInfo(f"Start import naar PostGIS in {connection_name}")

        self.import_parcels_wfs_to_postgis(connection_name, feedback, parameters, input_pol_source.id(), context)

        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "bgtinlooptabelnaarpostgis"

    def displayName(self):
        return self.tr("BGT Inlooptabel naar PostGIS")

    def group(self):
        return self.tr("afkoppelkanskaart")

    def groupId(self):
        return "afkoppelkanskaart"

    def shortHelpString(self):
        return self.tr("Importeren van inlooptabel in PostGIS")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return Inloop2PostGISAlgorithm()
    
    def import_parcels_wfs_to_postgis(self, connection_name:str, feedback, parameters, feature_source_id, context):
        feature_source = QgsProcessingFeatureSourceDefinition(source=feature_source_id, selectedFeaturesOnly=False)

        params = {
            'INPUT': feature_source,
            'DATABASE': connection_name,
            'SCHEMA': 'public',
            'TABLENAME': 'bgt_inlooptabel',
            'PRIMARY_KEY': 'fid',
            'GEOMETRY_COLUMN': 'geom',
            'ENCODING': 'UTF-8',
            'OVERWRITE': True,
            'CREATEINDEX': True,
            'LOWERCASE_NAMES': True,
            'DROP_STRING_LENGTH': True,
            'FORCE_SINGLEPART': False
        }

        processing.run("qgis:importintopostgis", params, context=context, feedback=feedback)
