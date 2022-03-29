# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Parcels2PostGISAlgorithm
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
from qgis.core import QgsProject
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingOutputBoolean
from qgis.PyQt.QtCore import QCoreApplication
import psycopg2
from ..constants import *
from ..database import get_pscycopg_connection_params
from ..database import get_postgis_layer
from afkoppelkansenkaart.processing.ordered_processing_algorithm import OrderedProcessingAlgorithm

from typing import List

class Parcels2PostGISAlgorithm(OrderedProcessingAlgorithm):

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
            QgsProcessingParameterMapLayer(self.INPUT_POL, self.tr("Perceel polygon"))
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

        feedback.pushInfo(f"Percelen ingeladen")

        self.subdivide_parcels(connection_name, feedback)
        
        feedback.pushInfo(f"Percelen onderverdeeld")

        postgis_parcel_source_layer = get_postgis_layer(
            connection_name,
            'kadastraal_perceel_subdivided',
            qgis_layer_name = "Perceel"
        )
        # QgsProject.instance().addMapLayer(postgis_parcel_source_layer, addToLegend=False)
        self.add_to_layer_tree_group(postgis_parcel_source_layer)

        success = True
        # Return the results of the algorithm. 
        return {self.OUTPUT: success}

    def name(self):
        return "parceltopostgis"

    def displayName(self):
        return self.tr("Percelen naar PostGIS")

    def group(self):
        return self.tr("afkoppelkanskaart")

    def groupId(self):
        return "afkoppelkanskaart"

    def shortHelpString(self):

        return self.tr("Importeren van geselecteerde percelen in PostGIS")

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return Parcels2PostGISAlgorithm()
    
    def add_to_layer_tree_group(self, layer):
        """
        Add a layer to the Afkoppelkansenkaart layer tree group
        """
        project = QgsProject.instance()
        project.addMapLayer(layer, addToLegend=False)
        self.layer_group.insertLayer(0, layer)

    def import_parcels_wfs_to_postgis(self, connection_name:str, feedback, parameters, feature_source_id, context):
        feature_source = QgsProcessingFeatureSourceDefinition(source=feature_source_id, selectedFeaturesOnly=True)

        params = {
            'INPUT': feature_source,
            'DATABASE': connection_name,
            'SCHEMA': 'public',
            'TABLENAME': 'kadastraal_perceel',
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

    def subdivide_parcels(self, connection_name:str, feedback):
        try:
            conn = psycopg2.connect(**get_pscycopg_connection_params(connection_name))
        except psycopg2.OperationalError:
            feedback.reportError("Kan geen verbinding maken met de database", True)
            return

        cursor = conn.cursor()
        sql_file_name = os.path.join(SQL_DIR, 'subdivide_parcels.sql')
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
