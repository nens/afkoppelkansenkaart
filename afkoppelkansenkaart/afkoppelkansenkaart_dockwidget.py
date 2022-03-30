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
    QgsProject,
    QgsVectorLayer,
)
from qgis.utils import iface
import processing
from database import get_pscycopg_connection_params
from database import get_postgis_layer

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
            self._parcel_layer_id = QgsProject.instance().mapLayersByName(PARCEL_WFS_LAYER_NAME)[0].id()
        except IndexError:  # No layer of that name exists:
            self._parcel_layer_id = None
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
        self.pushButton_reload.clicked.connect(self.reload_db)
        self.check_bewerkingen_ui()

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
        root = QgsProject.instance().layerTreeRoot()
        result = root.findGroup('Afkoppelkansenkaart')
        if not result:
            result = root.insertGroup(0, 'Afkoppelkansenkaart')
        return result

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

    def populate_combobox_postgis_databases(self):
        self.comboBox_PostGISDatabases.clear()
        # todo: enforce a proper functional order
        self.comboBox_PostGISDatabases.addItems(self.list_postgis_connections())

    def populate_combobox_bewerkingen(self, algos):
        
        # sort by order
        sorted_algo_list = sorted(algos, key=lambda x: x.order, reverse=False)
        for i, algo in enumerate(sorted_algo_list):
            self.comboBox_Bewerkingen.addItem(f'{1+i}. {algo.displayName()}', algo)
            
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
            self.check_bewerkingen_ui()

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
            self.check_bewerkingen_ui()

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
        algo_name = self.comboBox_Bewerkingen.currentData().name()
        algo = f'Afkoppelkansenkaart:{algo_name}'
        params = {}  # A dictionary to load some default value in the algo
        run_silent = False

        # in case certain data is available, prepopulate the parameters and
        # run the algo without dialog

        if algo_name is "bgtinlooptabelnaarpostgis":
            params['INPUT_DB'] = self.connection_name
        elif algo_name is "parceltopostgis":
            params['INPUT_DB'] = self.connection_name
            params['INPUT_POL'] = self.parcel_layer_id
            run_silent = True

        if run_silent:  
            processing.run(algo, params)
        else:
            processing.execAlgorithmDialog(algo, params)
        
    def reload_db(self):
        iface.messageBar().pushMessage(
            MESSAGE_CATEGORY,
            f"Reload DB",
            level=Qgis.Info,
            duration=10)

        postgis_parcel_source_layer = get_postgis_layer(
            self.connection_name,
             'kadastraal_perceel_subdivided',
             qgis_layer_name = PARCEL_POSTGIS_LAYER_NAME
        )
        self.postgis_parcel_source_layer_id = postgis_parcel_source_layer.id()
        # QgsProject.instance().addMapLayer(postgis_parcel_source_layer, addToLegend=False)
        self.add_to_layer_tree_group(postgis_parcel_source_layer)

    def add_parcel_wfs(self):
        if self.parcel_layer_id:
            QgsProject.instance().removeMapLayer(self.parcel_layer_id)
        vlayer = QgsVectorLayer(PARCELS_WFS_URL, PARCEL_WFS_LAYER_NAME, "WFS")
        self.add_to_layer_tree_group(vlayer)
        self.parcel_layer_id = vlayer.id()
        self.check_bewerkingen_ui()

    def postgis_connection_is_valid(self):
        try:
            conn = psycopg2.connect(**get_pscycopg_connection_params(self.connection_name))
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
            f"Geselecteerd algoritme: ({idx})",
            level=Qgis.Info,
            duration=10)
        self.textField_Uitleg.setPlainText(self.comboBox_Bewerkingen.currentData().shortHelpString())

    def check_bewerkingen_ui(self):
        complete = self.postgis_connection_is_valid() and self.parcel_layer_id is not None
        self.groupBox_ConnectedSurfaces.setEnabled(complete)
        if not complete:
            self.groupBox_ConnectedSurfaces.setToolTip(self.tr("Selecteer een database en importeer percelen"))
        else:
            self.groupBox_ConnectedSurfaces.setToolTip(self.tr("Selecteer een bewerking"))
