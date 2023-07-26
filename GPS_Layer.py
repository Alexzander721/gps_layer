# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GPSLayers
                                 A QGIS plugin
 Собирает слои для GPS
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-06-23
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Travin Alexzander/Roslesinforg
        email                : travin1995@inbox.ru
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import *
import processing
from qgis.core import (QgsApplication,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsFeature,
                       QgsExpression,
                       QgsField,
                       QgsFields,
                       QgsFeature,
                       QgsFeatureRequest,
                       QgsFeatureRenderer,
                       QgsGeometry,
                       QgsVectorDataProvider,
                       QgsVectorLayer,
                       QgsVectorFileWriter,
                       QgsWkbTypes,
                       QgsSpatialIndex,
                       QgsVectorLayerUtils,
                       QgsCoordinateTransform,
                       QgsMapLayerType,
                       QgsMapLayer,
                       QgsGeometry,
                       QgsProperty,
                       )
from .resources import *
from .GPS_Layer_dialog import GPSLayersDialog
import os.path


def message(title, text):
    msgBox = QMessageBox()
    msgBox.setWindowTitle(title)
    msgBox.setText(text)
    msgBox.exec()


class GPSLayers:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GPSLayers_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&Layers for GPS')

        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('GPSLayers', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):

        icon_path = ':/plugins/GPS_Layer/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'GPS'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Layers for GPS'),
                action)
            self.iface.removeToolBarIcon(action)

    def saveSHP(self, catalog, layers):
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = "ESRI Shapefile"
        save_options.fileEncoding = "UTF-8"
        save_options.ct = QgsCoordinateTransform(QgsProject.instance().crs(),
                                                 QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())
        transform_context = QgsProject.instance().transformContext()
        for layer in layers:
            if layer.type() == 0:
                error = QgsVectorFileWriter.writeAsVectorFormatV2(layer,
                                                                  catalog + "/WGS84_" + layer.name(),
                                                                  transform_context,
                                                                  save_options)
                if error[0] == QgsVectorFileWriter.NoError:
                    pass

    def remove(self, catalog, layers):
        for layer in layers:
            if layer.type() == 0:
                QgsProject.instance().addMapLayer(
                    QgsVectorLayer(f"{catalog}/WGS84_{layer.name()}.shp", f"WGS84_{layer.name()}", "ogr"))
                QgsProject.instance().removeMapLayer(layer)

    def dct(self):
        self.dlg.lineEdit.setText(QFileDialog.getExistingDirectory())

    def polkw(self, catalog, selectedLayerName):
        selectedfield = self.dlg.comboBox2.currentText()
        for layer in QgsProject.instance().layerTreeRoot().children():
            if layer.name() == f"WGS84_{selectedLayerName}":
                processing.run(
                    "native:dissolve",
                    {'INPUT': layer.layer(),
                     'FIELD': selectedfield,
                     'OUTPUT': f"{catalog}/WGS84_полигоны-квартала.shp"})
                player = QgsVectorLayer(f"{catalog}/WGS84_полигоны-квартала.shp", "WGS84_полигоны-квартала",
                                        "ogr")
                QgsProject.instance().addMapLayer(player)

    def set_crs(self, layers):
        [layer.setCrs(QgsProject.instance().crs()) for layer in layers if layer.type() == 0]

    def point_centroid(self, catalog, selectedLayerName):
        for lay in [f'WGS84_{selectedLayerName}', 'WGS84_полигоны-квартала']:
            processing.run(
                "native:pointonsurface",
                {'ALL_PARTS': QgsProperty.fromExpression('centroid($geometry)'),
                 'INPUT': lay,
                 'OUTPUT': f'{catalog}/{lay}№.shp'})
            QgsProject.instance().addMapLayer(QgsVectorLayer(f'{catalog}/{lay}№.shp', f'{lay}№', "ogr"))

    def choice_layer(self):
        self.dlg.comboBox.clear()
        [self.dlg.comboBox.addItem(layer.name(), layer) for layer in QgsProject.instance().mapLayers().values() if
         layer.type() == QgsMapLayer.VectorLayer and layer.wkbType() in [3, 6, 1006]]

    def change_field(self):
        self.dlg.comboBox2.clear()
        if self.dlg.comboBox.itemData(self.dlg.comboBox.currentIndex()) is not None:
            [self.dlg.comboBox2.addItem(field.name()) for field in
             self.dlg.comboBox.itemData(self.dlg.comboBox.currentIndex()).fields()]

    def run(self):
        self.dlg = GPSLayersDialog()
        self.dlg.lineEdit.clear()
        self.dlg.toolButton.clicked.connect(self.dct)
        self.dlg.comboBox.currentIndexChanged.connect(self.change_field)
        self.choice_layer()
        self.change_field()
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            selectedLayer = self.dlg.comboBox.itemData(self.dlg.comboBox.currentIndex())
            selectedLayerName = self.dlg.comboBox.itemData(self.dlg.comboBox.currentIndex()).name()
            catalog = self.dlg.lineEdit.text()
            if catalog == '':
                message("Ошибка!", "Папка назначения не задана!")
            elif selectedLayer.wkbType() == 3 or selectedLayer.wkbType() == 6:
                self.set_crs(self.iface.mapCanvas().layers())
                self.saveSHP(catalog, self.iface.mapCanvas().layers())
                self.remove(catalog, self.iface.mapCanvas().layers())
                self.polkw(catalog, selectedLayerName)
                if self.dlg.checkBox.isChecked():
                    self.point_centroid(catalog, selectedLayerName)
                message("Готово!", f"Результирующие слои сохранены: {catalog}")
        else:
            pass
