# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PercentageCultivationAlgorithm
                                 A QGIS plugin
 Calculate percentage cultivation
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

from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProject
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
import psycopg2
from ..constants import *
from ..database import get_pscycopg_connection_params
from ..database import get_postgis_layer

class PercentageCultivationAlgorithm(QgsProcessingAlgorithm):

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
    
        self.calculate_percentage(connection_name, feedback)
        
        feedback.pushInfo(f"Percentage bepaald")

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
        return "percentagecultivation"

    def displayName(self):
        return self.tr("Percentage bebouwing")

    def group(self):
        return self.tr("afkoppelkanskaart")

    def groupId(self):
        return "afkoppelkanskaart"

    def shortHelpString(self):

        return self.tr("Bepalen van percentage bebouwing")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return PercentageCultivationAlgorithm()
    
    def add_to_layer_tree_group(self, layer):
        """
        Add a layer to the Afkoppelkansenkaart layer tree group
        """
        project = QgsProject.instance()
        project.addMapLayer(layer, addToLegend=False)
        self.layer_group.insertLayer(0, layer)

    def calculate_percentage(self, connection_name:str, feedback):
        try:
            conn = psycopg2.connect(**get_pscycopg_connection_params(connection_name))
        except psycopg2.OperationalError:
            feedback.reportError("Kan geen verbinding maken met de database", True)
            return

        cursor = conn.cursor()
        sql_file_name = os.path.join(SQL_DIR, 'built_up_percentage.sql')
        with open(sql_file_name, 'r') as sql_file:
            sql = sql_file.read()
        cursor.execute(sql)
        conn.commit()
        conn.close()

    @property
    def layer_group(self):
        root = QgsProject.instance().layerTreeRoot()
        _layer_group = root.findGroup('Afkoppelkansenkaart')
        if not _layer_group:
            _layer_group = root.insertGroup(0, 'Afkoppelkansenkaart')
        return _layer_group

    def add_to_layer_tree_group(self, layer):
        """
        Add a layer to the layer tree group
        """
        project = QgsProject.instance()
        project.addMapLayer(layer, addToLegend=False)
        self.layer_group.insertLayer(0, layer)

