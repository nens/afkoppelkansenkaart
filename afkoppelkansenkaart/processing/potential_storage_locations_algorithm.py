# -*- coding: utf-8 -*-

"""
/***************************************************************************
 PotentialStorageLocationAlgorithm
                                 A QGIS plugin
 Calculate potential storage locations
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
__date__ = "2022-03-01"
__copyright__ = "(C) 2022 by Nelen en Schuurmans"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis.core import QgsProject
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
from ..constants import *
from ..database import execute_sql_script, get_postgis_layer
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm

class PotentialStorageLocationAlgorithm(OrderedProcessingAlgorithm):

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
        
        connection_name = self.parameterAsConnectionName(
            parameters, self.INPUT_DB, context
        )


        success = False

        feedback.pushInfo(f"Bepalen locaties")
   
        execute_sql_script(connection_name, 'derive_potential_storage_locations', feedback)
        
        feedback.pushInfo(f"Locaties bepaald")

        postgis_parcel_source_layer = get_postgis_layer(
            connection_name,
            'potentiele_bergingslocaties',
            qgis_layer_name = 'Potentiële bergingslocaties'
        )

        self.add_to_layer_tree_group(postgis_parcel_source_layer)

        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "potentialstorage"

    def displayName(self):
        return self.tr("Potentiële bergingslocaties")

    def group(self):
        return self.tr("Percelen verrijken")

    def groupId(self):
        return "Percelen verrijken"

    def shortHelpString(self):
        return self.tr("Bepalen van potentiële bergingslocaties")
    
    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return PotentialStorageLocationAlgorithm()

    def add_to_layer_tree_group(self, layer):
        """
        Add a layer to the Afkoppelkansenkaart layer tree group
        """
        project = QgsProject.instance()
        project.addMapLayer(layer, addToLegend=False)
        self.layer_group.insertLayer(0, layer)

    @property
    def layer_group(self):
        root = QgsProject.instance().layerTreeRoot()
        _layer_group = root.findGroup('Afkoppelkansenkaart')
        if not _layer_group:
            _layer_group = root.insertGroup(0, 'Afkoppelkansenkaart')
        return _layer_group