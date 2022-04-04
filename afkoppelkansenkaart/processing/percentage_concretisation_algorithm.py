# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PercentageConcretisationAlgorithm
                                 A QGIS plugin
 Calculate percentage concretisation
                              -------------------
        begin                : 2022-03-01
        copyright            : (C) 2022 by Nelen en Schuurmans
        email                : leendert.vanwolfswinkel@nelen-schuurmans.nl

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
__date__ = "2022-03-01"
__copyright__ = "(C) 2021 by Nelen en Schuurmans"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
from ..constants import *
from ..database import execute_sql_script
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm


class PercentageConcretisationAlgorithm(OrderedProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = "OUTPUT"
    INPUT_DB = "INPUT_DB"
    INPUT_PER = "INPUT_PER"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        
        self.addParameter(
            QgsProcessingParameterProviderConnection(self.INPUT_DB, self.tr("Connectie naam"), "postgres")
        )

        param = QgsProcessingParameterNumber(self.INPUT_PER, self.tr("Groen percentage"), type=QgsProcessingParameterNumber.Double, 
                minValue=0.0,
                maxValue=100.0, 
                defaultValue=50.0
        )
        param.setMetadata( {'widget_wrapper':
        { 'decimals': 2 }})

        self.addParameter(param)
        

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
        
        feedback.pushInfo(f"Start algo")

        connection_name = self.parameterAsConnectionName(
            parameters, self.INPUT_DB, context
        )

        percentage = self.parameterAsDouble(parameters, 
            self.INPUT_PER, context
        )

        feedback.pushInfo(f"Percentage: {percentage}")
    
        execute_sql_script(connection_name, 'parcel_geometry_without_buildings', feedback)
        
        feedback.pushInfo(f"Gebouwen verwijderd")

        self.calculate_percentage(connection_name, feedback)

        # postgis_parcel_source_layer = self.get_postgis_layer(
        #     connection_name,
        #     'kadastraal_perceel_subdivided',
        #     qgis_layer_name = "Perceel"
        # )

        # self.add_to_layer_tree_group(postgis_parcel_source_layer)

        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "percentageconcretisation"

    def displayName(self):
        return self.tr("Percentage verharding")

    def group(self):
        return self.tr("afkoppelkanskaart")

    def groupId(self):
        return "afkoppelkanskaart"

    def shortHelpString(self):
        return self.tr("Bepalen van percentage verhardingouwing")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return PercentageConcretisationAlgorithm()
    
    def calculate_percentage(self, connection_name:str, feedback):
        pass



