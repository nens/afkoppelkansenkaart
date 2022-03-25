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
from qgis.core import Qgis
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingFeatureSourceDefinition
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProviderConnectionException
from qgis.core import QgsProject
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingOutputBoolean
from qgis.core import QgsProcessingFeedback
from qgis.core import QgsDataSourceUri
from qgis.core import QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QProgressBar
import psycopg2
from ..constants import *

from typing import List

class Parcels2PostGISAlgorithm(QgsProcessingAlgorithm):

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
            QgsProcessingParameterFeatureSource(self.INPUT_POL, self.tr("Perceel polygon"), [QgsProcessing.TypeVectorPolygon] )
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
 
        iface.messageBar().pushMessage(
            MESSAGE_CATEGORY,
            "Start inladen percelen",
            level=Qgis.Success,
            duration=3
        )

        connection_name = self.parameterAsConnectionName(
            parameters, self.INPUT_DB, context
        )

        input_pol_source = self.parameterAsSource(
            parameters,
            self.INPUT_POL,
            context
        )

        if input_pol_source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POL))

        self.import_parcels_wfs_to_postgis(connection_name)
        self.subdivide_parcels(connection_name)
        
        postgis_parcel_source_layer = self.get_postgis_layer(
            'kadastraal_perceel_subdivided',
            qgis_layer_name = "perceel"
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

    def import_parcels_wfs_to_postgis(self, connection_name:str):
        feature_source = QgsProcessingFeatureSourceDefinition(source=self.INPUT_POL, selectedFeaturesOnly=True)
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
        # Progress bar
        iface.messageBar().clearWidgets()
        progress_message_bar = iface.messageBar()
        # progress_message_bar.createMessage('Import to PostGIS')
        progressbar = QProgressBar()
        progress_message_bar.pushWidget(progressbar)

        # Processing feedback
        def progress_changed(progress):
            progressbar.setValue(progress)

        feedback = QgsProcessingFeedback()
        feedback.progressChanged.connect(progress_changed)
        processing.runAndLoadResults("qgis:importintopostgis", params, feedback=feedback)
        iface.messageBar().clearWidgets()
        iface.messageBar().pushMessage(
            MESSAGE_CATEGORY,
            "Percelen ingeladen in PostGIS database",
            level=Qgis.Success,
            duration=3
        )
        # context = QgsProcessingContext()
        # feedback = QgsProcessingFeedback()
        # alg = QgsApplication.instance().processingRegistry().algorithmById('native:importintopostgis')
        # task = QgsProcessingAlgRunnerTask(alg, params, context, feedback)
        # # task.executed.connect(partial(task_finished, context))
        # QgsApplication.taskManager().addTask(task)

    def subdivide_parcels(self, connection_name:str):
        try:
            conn = psycopg2.connect(**self.get_pscycopg_connection_params(connection_name))
        except psycopg2.OperationalError:
            iface.messageBar().pushMessage(
                MESSAGE_CATEGORY,
                "Kan geen verbinding maken met de database",
                level=Qgis.Warning,
                duration=3
            )
            return
        cursor = conn.cursor()
        sql_file_name = os.path.join(SQL_DIR, 'subdivide_parcels.sql')
        with open(sql_file_name, 'r') as sql_file:
            sql = sql_file.read()
        cursor.execute(sql)
        conn.commit()
        conn.close()
    
    def get_postgis_layer(self, pg_layer_name: str, qgis_layer_name: str = None, geometry_column_name='geom'):
        if not qgis_layer_name:
            qgis_layer_name = pg_layer_name
        uri = QgsDataSourceUri()
        params = self.get_pscycopg_connection_params(self.connection_name)
        uri.setConnection(
            aHost=params['host'],
            aPort=params['port'],
            aDatabase=params['dbname'],
            aUsername=params['user'],
            aPassword=params['password']
        )
        uri.setDataSource(
            aSchema='public',
            aTable=pg_layer_name,
            aGeometryColumn=geometry_column_name
        )

        layer = QgsVectorLayer(uri.uri(), qgis_layer_name, "postgres")
        return layer

    def add_to_layer_tree_group(self, layer):
        """
        Add a layer to the layer tree group
        """
        project = QgsProject.instance()
        project.addMapLayer(layer, addToLegend=False)
        self.layer_group.insertLayer(0, layer)