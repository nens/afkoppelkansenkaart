# -*- coding: utf-8 -*-

"""
/***************************************************************************
 TransferSewerageTypeAlgorithm
                                 A QGIS plugin
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

from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
from ..database import execute_sql_script
from ..constants import *
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm

class TransferSewerageTypeAlgorithm(OrderedProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT_DB = "INPUT_DB"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
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

        success = False
    
        execute_sql_script(connection_name, 'sewerage_type', feedback)
        
        success = True

        return {self.OUTPUT: success}

    def name(self):
        return "transferseweragetype"

    def displayName(self):
        return self.tr("Overnemen stelseltype")

    def group(self):
        return self.tr("afkoppelkanskaart")

    def groupId(self):
        return "afkoppelkanskaart"

    def shortHelpString(self):
        return self.tr("Overnemen van riool stelseltype")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return TransferSewerageTypeAlgorithm()
