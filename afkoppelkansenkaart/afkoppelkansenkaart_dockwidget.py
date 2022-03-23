# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AfkoppelKansenKaartDockWidget
                                 A QGIS plugin
 Bepaal de effectiviteit en kansrijkheid van het afkoppelen van de riolering
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-01-12
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Nelen & Schuurmans
        email                : info@nelen-schuurmans.nl
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

import os
import sys
sys.path.append(os.path.dirname(__file__))

import db_manager.db_plugins.postgis.connector as con
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtWidgets import QProgressBar, QFileDialog
from qgis.PyQt.QtCore import pyqtSignal, QSettings
from qgis.core import (
    NULL,
    Qgis,
    QgsFeature,
    QgsFields,
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsMapLayerProxyModel,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeatureSourceDefinition,
    QgsProcessingFeedback,
    QgsApplication,
    QgsAuthMethodConfig,
    QgsDataSourceUri
)
from qgis.utils import iface
import processing

import psycopg2

from .constants import *
from afkoppelkansenkaart.database import *
from qgis.core import QgsProcessingProvider

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'afkoppelkansenkaart_dockwidget_base.ui'))


class AfkoppelKansenKaartDockWidget(QtWidgets.QDockWidget,FORM_CLASS):
    closingPlugin=pyqtSignal()
    
    def __init__(self,parent, provider):
        """Constructor."""
        super(AfkoppelKansenKaartDockWidget,self).__init__(parent)

        try:
            self._parcel_layer_id = QgsProject.instance().mapLayersByName('Kadastraal perceel')[0].id()
        except IndexError:  # No layer of that name exists:
            self._parcel_layer_id = None
        self._layer_group = None
        self.db = None

        self.setupUi(self)
        self.pushButton_Nieuw.clicked.connect(self.nieuw_clicked)
        self.pushButton_Open.clicked.connect(self.open_clicked)
        self.pushButton_PercelenWFS.clicked.connect(self.add_parcel_wfs)
        self.comboBox_PostGISDatabases.currentIndexChanged.connect(self.update_postgis_connection_status)
        self.populate_combobox_postgis_databases()
        self.pushButton_Play.clicked.connect(self.play_clicked)
        self.populate_combobox_bewerkingen(provider.algorithms())
        self.comboBox_Bewerkingen.currentIndexChanged.connect(self.update_bewerking)

    def closeEvent(self,event):
        self.closingPlugin.emit()
        event.accept()

    @property
    def connection_name(self):
        return self.comboBox_PostGISDatabases.currentText()

    @property
    def parcel_layer_id(self):
        if QgsProject.instance().mapLayer(self._parcel_layer_id):
            return self._parcel_layer_id
        else:
            return None

    @parcel_layer_id.setter
    def parcel_layer_id(self, id: str):
        self._parcel_layer_id = id

    @property
    def layer_group(self):
        if not self._layer_group:
            root = QgsProject.instance().layerTreeRoot()
            self._layer_group = root.findGroup('Afkoppelkansenkaart')
            if not self._layer_group:
                self._layer_group = root.insertGroup(0, 'Afkoppelkansenkaart')
        return self._layer_group

    def add_to_layer_tree_group(self, layer):
        """
        Add a layer to the Afkoppelkansenkaart layer tree group
        """
        project = QgsProject.instance()
        project.addMapLayer(layer, addToLegend=False)
        self.layer_group.insertLayer(0, layer)

    def list_postgis_connections(self):
        s = QSettings()
        s.beginGroup("PostgreSQL/connections")
        result = s.childGroups()
        s.endGroup()
        return result

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

    def populate_combobox_postgis_databases(self):
        self.comboBox_PostGISDatabases.clear()
        self.comboBox_PostGISDatabases.addItems(self.list_postgis_connections())

    def populate_combobox_bewerkingen(self, algos):
        for i, algo in enumerate(algos):
            self.comboBox_Bewerkingen.addItem(f'{1+i}. {algo.name()}', algo)
            
        self.update_bewerking(0)

    def nieuw_clicked(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Nieuwe afkoppelkansenkaart", "", "GeoPackage (*.gpkg)")
        if filename:
            iface.messageBar().pushMessage(
                MESSAGE_CATEGORY,
                f"Afkoppelkansenkaart geopackage aangemaakt! ({filename})",
                level=Qgis.Success,
                duration=10
            )
            self.db = AfkoppelKansenKaartDatabase()
            self.db.create_datasource(filename)
            self.db.epsg = 28992
            self.db.create_schema()
            self.db.initialise()
            self.db.create_pivot_view()
            self.add_afkoppelkansenkaart_layer()

    def open_clicked(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Nieuwe afkoppelkansenkaart", "", "GeoPackage (*.gpkg)")
        if filename:
            if self.db:
                if filename == self.db.gpkg_path:
                    iface.messageBar().pushMessage(
                        MESSAGE_CATEGORY,
                        f"Deze afkoppelkansenkaart was reeds geopend. ({filename})",
                        level=Qgis.Info,
                        duration=10
                    )
                    return
            self.db = AfkoppelKansenKaartDatabase()
            self.db.set_datasource(filename)
            iface.messageBar().pushMessage(
                MESSAGE_CATEGORY,
                f"Afkoppelkansenkaart geopend. ({filename})",
                level=Qgis.Info,
                duration=10
            )
            self.add_afkoppelkansenkaart_layer()

    def add_afkoppelkansenkaart_layer(self):
        if self.db.gpkg_path:
            layer = QgsVectorLayer(str(self.db.gpkg_path) + "|layername=afkoppelkansenkaart", "Afkoppelkansenkaart")
            self.add_to_layer_tree_group(layer=layer)
        else:
            iface.messageBar().pushMessage(
                MESSAGE_CATEGORY,
                "Laad eerst een afkoppelkansenkaart in",
                level=Qgis.Info,
                duration=3
            )

    def play_clicked(self):
        # Run the selected Processor
        iface.messageBar().pushMessage(
            MESSAGE_CATEGORY,
            f"Start algoritme: ({self.comboBox_Bewerkingen.currentText()})",
            level=Qgis.Info,
            duration=10)
            
        algo_name = self.comboBox_Bewerkingen.currentData().name()
        params = {}  # A dictionary to load some default value in the dialog
        processing.execAlgorithmDialog(f'Afkoppelkansenkaart:{algo_name}', {})
        
        # self.import_parcels_wfs_to_postgis()
        # self.subdivide_parcels()
        # postgis_parcel_source_layer = self.get_postgis_layer(
        #     'kadastraal_perceel_subdivided',
        #     qgis_layer_name = "Perceel (PostGIS)"
        # )
        # self.postgis_parcel_source_layer_id = postgis_parcel_source_layer.id()
        # # QgsProject.instance().addMapLayer(postgis_parcel_source_layer, addToLegend=False)
        # self.add_to_layer_tree_group(postgis_parcel_source_layer)

    @staticmethod
    def get_pscycopg_connection_params(connection_name: str):
        s = QSettings()
        s.beginGroup(f"PostgreSQL/connections/{connection_name}")
        result = {
            'host': s.value('host'),
            'port': s.value('port'),
            'user': s.value('username'),
            'password': s.value('password'),
            'dbname': s.value('database'),
        }
        if result['password'] == '':
            authcfg = s.value('authcfg')
            auth_mgr = QgsApplication.authManager()
            auth_method_config = QgsAuthMethodConfig()
            auth_mgr.loadAuthenticationConfig(authcfg, auth_method_config, True)
            config_map = auth_method_config.configMap()
            result['user'] = config_map['username']
            result['password'] = config_map['password']
        return result

    def add_parcel_wfs(self):
        if self.parcel_layer_id:
            QgsProject.instance().removeMapLayer(self.parcel_layer_id)
        vlayer = QgsVectorLayer(PARCELS_WFS_URL, "Kadastraal perceel", "WFS")
        self.add_to_layer_tree_group(vlayer)
        self.parcel_layer_id = vlayer.id()

    def postgis_connection_is_valid(self):
        try:
            conn = psycopg2.connect(**self.get_pscycopg_connection_params(self.connection_name))
        except psycopg2.OperationalError:
            return False
        conn.close()
        return True

    def update_postgis_connection_status(self):
        if self.postgis_connection_is_valid():
            self.label_StatusValue.setText('Database ready')
        else:
            self.label_StatusValue.setText('Invalid connection details')
            
    def update_bewerking(self, idx):
        iface.messageBar().pushMessage(
            MESSAGE_CATEGORY,
            f"Gelesteerd algoritme: ({idx})",
            level=Qgis.Info,
            duration=10)
        self.textField_Uitleg.setPlainText(self.comboBox_Bewerkingen.currentData().shortHelpString())
        #self.textField_Uitleg.setPlainText(f'Uitl3eg over {idx}')

    def import_parcels_wfs_to_postgis(self):
        if self.parcel_layer_id:
            feature_source = QgsProcessingFeatureSourceDefinition(source=self.parcel_layer_id, selectedFeaturesOnly=True)
            params = {
                'INPUT': feature_source,
                'DATABASE': self.connection_name,
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

        else:
            iface.messageBar().pushMessage(
                MESSAGE_CATEGORY,
                "Laad eerst de percelen in via 'Laad percelen (WFS)'",
                level=Qgis.Warning,
                duration=3  # wat langer zodat gebruiker tijd heeft om op linkje te klikken
            )

    def subdivide_parcels(self):
        try:
            conn = psycopg2.connect(**self.get_pscycopg_connection_params(self.connection_name))
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

    def import_subdivided_parcels_to_akk(self):
        src_layer = QgsProject.instance().mapLayer(self.postgis_parcel_source_layer_id)

        tgt_layer = QgsVectorLayer(str(self.db.gpkg_path) + "|layername=perceel", "perceel")
        target_fields = QgsFields(tgt_layer.fields())
        tgt_layer.startEditing()
        tgt_features = dict()
        for i, src_feature in enumerate(src_layer.getFeatures()):
            tgt_features[i] = QgsFeature()
            tgt_features[i].setFields(target_fields)
            tgt_geometry = src_feature.geometry()
            tgt_features[i].setGeometry(tgt_geometry)

        success = tgt_layer.addFeatures(list(tgt_features.values()))
        print(success)
        tgt_layer.commitChanges()
        self.db.update_gpkg_ogr_contents(table_name=self.db.result_view_name)

