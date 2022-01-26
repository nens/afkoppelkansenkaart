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

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings
from qgis.core import QgsProject,QgsVectorLayer,QgsRasterLayer,QgsMapLayerProxyModel, QgsProcessingFeatureSourceDefinition

import processing

import psycopg2

# Initialize Qt resources from file resources.py
from .constants import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'afkoppelkansenkaart_dockwidget_base.ui'))


class AfkoppelKansenKaartDockWidget(QtWidgets.QDockWidget,FORM_CLASS):
    closingPlugin=pyqtSignal()
    
    def __init__(self,parent=None):
        """Constructor."""
        super(AfkoppelKansenKaartDockWidget,self).__init__(parent)

        self.parcel_layer_id = None

        self.setupUi(self)
        self.pushButton_PercelenWFS.clicked.connect(self.add_parcel_wfs)
        self.pushButton_CheckConnection.clicked.connect(self.update_postgis_connection_status)
        self.populate_combobox_postgis_databases()

    def closeEvent(self,event):
        self.closingPlugin.emit()
        event.accept()

    def list_postgis_connections(self):
        s = QSettings()
        s.beginGroup("PostgreSQL/connections")
        result = s.childGroups()
        s.endGroup()
        return result

    def populate_combobox_postgis_databases(self):
        self.comboBox_PostGISDatabases.clear()
        self.comboBox_PostGISDatabases.addItems(self.list_postgis_connections())

    def add_parcel_wfs(self):
        if self.parcel_layer_id:
            QgsProject.instance().removeMapLayer(self.parcel_layer_id)
        vlayer = QgsVectorLayer(PARCELS_WFS_URL, "Kadastraal perceel", "WFS")
        QgsProject.instance().addMapLayer(vlayer)
        self.parcel_layer_id = vlayer.id()

    def get_postgis_connection_params(self):
        host = self.lineEdit_Host.text()
        port = self.spinBox_Port.value()
        user = self.lineEdit_User.text()
        password = self.lineEdit_Password.text()
        dbname = self.lineEdit_Database.text()

        db_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'dbname': dbname,
        }
        return db_params

    def postgis_connection_is_valid(self):
        try:
            conn = psycopg2.connect(**self.get_postgis_connection_params())
        except psycopg2.OperationalError:
            return False
        conn.close()
        return True

    def update_postgis_connection_status(self):
        if self.postgis_connection_is_valid():
            self.label_StatusValue.setText('Valid connection details')
        else:
            self.label_StatusValue.setText('Invalid connection details')

    def import_parcels_wfs_to_postgis(self):
        feature_source = QgsProcessingFeatureSourceDefinition(source=self.parcel_layer_id, selectedFeaturesOnly = True)
        processing_args = {
            'INPUT': feature_source,
            'DATABASE': 'localhost - sandbox',
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
        processing.run("qgis:importintopostgis",
