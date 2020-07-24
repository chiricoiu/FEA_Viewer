# -*- coding:Utf8 -*-

__author__ = "Christian Hiricoiu"
__email__ = "christian.hiricoiu@gmail.com"
__licence__ = "GPL"
__version__ = "1.0"

"""
Programme de visualisation d'analyse de calcul éléments finis.

Ce programme a été créé dans le but de faciliter l'analyse post traitement d'un calcul de structure en matériaux 
composites. Il récupère en entrée une base de données (database.db) contenant les différents noeuds du maillage ainsi 
que les valeurs des différents critères regardés dans les différents drappages de la structure composite.

Ce programme est consitué d'une interface graphique qui permet ensuite d'afficher les différents plis de la structure
composite définis dans la database, d'observer les gradients d'évolution des critères et de jouer sur les échelles.
"""

""" import des librairies externes """
from PyQt5 import QtWidgets, QtSql, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from matplotlib import colors, cm
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from itertools import repeat
from multiprocessing import Pool, cpu_count, freeze_support

import tkinter as tk
from tkinter import filedialog

import os
import sqlite3
import sys

import matplotlib as mpl
import numpy as np
import pandas as pd
import pptk  # https://github.com/heremaps/pptk/blob/master/pptk/viewer/viewer.py
import win32gui
import time

""" import des librairies internes """
import designer

""" variables globales """
P = ""
v = ""
listofclouds = []
cloud = []
axis = []

""" Définition des classes """


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure(figsize=(9, 1.5))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title('')
        self.Norm = mpl.colors.Normalize(vmin=0, vmax=1)
        self.fig.colorbar(cm.ScalarMappable(norm=self.Norm, cmap='jet'), cax=self.ax, orientation='horizontal')
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.15, top=0.80)
        FigureCanvasQTAgg.__init__(self, self.fig)
        FigureCanvasQTAgg.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)


class Mplwidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QtWidgets.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)


class MainWindow(QtWidgets.QMainWindow, designer.Ui_MainWindow):
    def __init__(self, database_path):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        # initialisation du tableview et association avec le fichier database.db
        self.database_path = database_path  # chargement du nom complet de la base de données
        self.db = QtSql.QSqlDatabase.addDatabase("QSQLITE")  # lecture de la base de données
        self.db.setDatabaseName(self.database_path)
        self.db.open()
        self.model = QtSql.QSqlTableModel(self, self.db)  # association du modèle de données à la table
        self.tableView_points.setModel(self.model)
        self.model.setTable("Ply_1")
        self.model.select()

        # initialisation du tablewidget des différents plis
        global listofclouds
        self.tableWidget_ply.setRowCount(len(listofclouds))
        self.tableWidget_ply.setColumnCount(4)
        for i in range(0, self.tableWidget_ply.rowCount()):
            attrib = listofclouds[i][1]
            self.tableWidget_ply.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.tableWidget_ply.setItem(i, 1, QTableWidgetItem(str(round(max(attrib[0]), 3))))
            self.tableWidget_ply.setItem(i, 2, QTableWidgetItem(str(round(max(attrib[1]), 3))))
            self.tableWidget_ply.setItem(i, 3, QTableWidgetItem(str(round(max(attrib[2]), 3))))

        # initialisation de l'intégration du viewer dans la fenêtre
        self.cloudpoint = np.random.rand(0, 3)
        self.v = pptk.viewer(self.cloudpoint)
        self.viewer_widget = QtWidgets.QWidget(self.viewer_frame)
        hwnd = win32gui.FindWindowEx(0, 0, None, "viewer")
        self.window = QtGui.QWindow.fromWinId(hwnd)
        self.windowcontainer = self.createWindowContainer(self.window, self.viewer_widget)
        self.gridLayout.addWidget(self.windowcontainer, 0, 0, 1, 1)
        self.windowcontainer.setFocusPolicy(QtCore.Qt.StrongFocus)

        # controls
        self.selectionmodelpoint = self.tableView_points.selectionModel()
        self.selectionmodelpoint.selectionChanged.connect(self.select_point)
        self.selectionmodelply = self.tableWidget_ply.selectionModel()
        self.selectionmodelply.selectionChanged.connect(self.plot_data)
        self.crit_cbbox.currentIndexChanged.connect(self.change_scale)
        self.scaleButton.clicked.connect(self.rescale)

    def rescale(self):
        global v, axis
        try:
            if self.minscaleLE.text() != "":
                minval = float(self.minscaleLE.text())
            else:
                minval = axis[self.crit_cbbox.currentIndex()][0]

            if self.maxscaleLE.text() != "":
                maxval = float(self.maxscaleLE.text())
            else:
                maxval = axis[self.crit_cbbox.currentIndex()][1]
            try:
                axis[self.crit_cbbox.currentIndex()] = [minval, maxval]
                labelx = ["attribut 1 : Tsai-Hill",
                          "attribut 2 : Tsai-Wu",
                          "attribut 3 : Von Mises (MPa)",
                          "attribut 4 : déplacements (mm)"]
                self.mpl_widget.canvas.ax.clear()
                self.mpl_widget.canvas.ax.set_title(labelx[self.crit_cbbox.currentIndex()])
                self.mpl_widget.canvas.Norm = mpl.colors.Normalize(vmin=axis[self.crit_cbbox.currentIndex()][0],
                                                                   vmax=axis[self.crit_cbbox.currentIndex()][1])
                self.mpl_widget.canvas.fig.colorbar(cm.ScalarMappable(norm=self.mpl_widget.canvas.Norm,
                                                                      cmap='jet'),
                                                    cax=self.mpl_widget.canvas.ax,
                                                    orientation='horizontal')
                self.mpl_widget.canvas.draw()
                v.set(curr_attribute_id=self.crit_cbbox.currentIndex())
                v.set(color_map_scale=[minval, maxval])
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    def change_scale(self):
        global v, listofclouds, axis
        try:
            index = self.tableWidget_ply.selectionModel().currentIndex()
            attrib = listofclouds[int(index.sibling(index.row(), 0).data()) - 1][1]
            axis = [[min(attrib[0]), max(attrib[0])],
                    [min(attrib[1]), max(attrib[1])],
                    [min(attrib[2]), max(attrib[2])],
                    [min(attrib[3]), max(attrib[3])]]
            labelx = ["attribut 1 : Tsai-Hill",
                      "attribut 2 : Tsai-Wu",
                      "attribut 3 : Von Mises (MPa)",
                      "attribut 4 : déplacements (mm)"]
            self.mpl_widget.canvas.ax.clear()
            self.mpl_widget.canvas.ax.set_title(labelx[self.crit_cbbox.currentIndex()])
            self.mpl_widget.canvas.Norm = mpl.colors.Normalize(vmin=axis[self.crit_cbbox.currentIndex()][0],
                                                               vmax=axis[self.crit_cbbox.currentIndex()][1])
            self.mpl_widget.canvas.fig.colorbar(cm.ScalarMappable(norm=self.mpl_widget.canvas.Norm,
                                                                  cmap='jet'),
                                                cax=self.mpl_widget.canvas.ax,
                                                orientation='horizontal')
            self.mpl_widget.canvas.draw()
            self.minscaleLE.setText(str(round(axis[self.crit_cbbox.currentIndex()][0], 3)))
            self.maxscaleLE.setText(str(round(axis[self.crit_cbbox.currentIndex()][1], 3)))
            v.set(curr_attribute_id=self.crit_cbbox.currentIndex())
            v.set(color_map_scale=axis[self.crit_cbbox.currentIndex()])
        except Exception as e:
            print(e)

    def select_point(self):
        global P, v
        try:
            index = self.tableView_points.selectionModel().currentIndex()
            x = index.sibling(index.row(), 0).data()
            y = index.sibling(index.row(), 1).data()
            z = index.sibling(index.row(), 2).data()
            point_index = P.tolist().index([x, y, z])
            v.set(selected=point_index)
            v.set(lookat=(x, y, z))
        except Exception as e:
            print(e)

    def plot_data(self):
        index = self.tableWidget_ply.selectionModel().currentIndex()
        self.model.setTable("Ply_" + str(index.sibling(index.row(), 0).data()))
        self.model.select()

        global v, P, listofclouds
        try:
            P = listofclouds[int(index.sibling(index.row(), 0).data()) - 1][0]
            attrib = listofclouds[int(index.sibling(index.row(), 0).data()) - 1][1]
            v = pptk.viewer(P)
            v.attributes(attrib[0], attrib[1], attrib[2], attrib[3])
            v.set(point_size=0.8)

            self.viewer_widget = QtWidgets.QWidget(self.viewer_frame)
            hwnd = win32gui.FindWindowEx(0, 0, None, "viewer")
            self.window = QtGui.QWindow.fromWinId(hwnd)
            self.window.setFlags(QtCore.Qt.FramelessWindowHint)
            self.windowcontainer = self.createWindowContainer(self.window, self.viewer_widget)
            self.gridLayout.addWidget(self.windowcontainer, 0, 0, 1, 1)
            self.windowcontainer.setFocusPolicy(QtCore.Qt.TabFocus)
            self.crit_cbbox.setCurrentIndex(1)
            self.change_scale()
            v.set(curr_attribute_id=self.crit_cbbox.currentIndex())
        except Exception as e:
            print(e)


""" définition des fonctions """


def path_database():
    root = tk.Tk()
    root.withdraw()
    dbpath = filedialog.askopenfilename(title="Select database",
                                        filetypes=[("Database Files", "*.db")],
                                        parent=root)
    return dbpath


def load_clouds(db_path, nb_ply):
    try:
        global listofclouds
        p = Pool(processes=cpu_count())
        data = p.starmap(load_cloud, zip(repeat(db_path), range(1, nb_ply + 1)))
        for cloudelement in data:
            listofclouds.append(cloudelement)
    except Exception as e:
        print(e)


def load_cloud(db_path, numply):
    connector = sqlite3.connect(db_path)
    query = "SELECT * FROM Ply_" + str(numply)
    df = pd.read_sql_query(query, connector)
    xlist, ylist, zlist, tsaihill, tsaiwu, vonmises, displacement = [], [], [], [], [], [], []
    for node in range(0, len(df)):
        xlist.append(float(df.x[node]))
        ylist.append(float(df.y[node]))
        zlist.append(float(df.z[node]))
        tsaihill.append(float(df.Tsai_Hill[node]))
        tsaiwu.append(float(df.Tsai_Wu[node]))
        vonmises.append(float(df.Von_Mises[node]))
        displacement.append(float(df.displacement[node]))
        pass
    attrib_tsaihill = np.transpose(np.array(tsaihill))
    attrib_tsaiwu = np.transpose(np.array(tsaiwu))
    attrib_vonmises = np.transpose(np.array(vonmises))
    attrib_displacement = np.transpose(np.array(displacement))
    listattrib = [attrib_tsaihill, attrib_tsaiwu, attrib_vonmises, attrib_displacement]
    points = np.transpose(np.array([xlist, ylist, zlist]))
    cloud_ply = [points, listattrib]
    return cloud_ply


def count_tables(database_path):
    connector = sqlite3.connect(database_path)
    cursor = connector.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return len(cursor.fetchall())


def list_n_elem_max(array, n):
    list_val = array.tolist()
    list_val_max = []
    for i in range(0, n):
        val_max = 0
        for j in list_val:
            if j > val_max:
                val_max = j
        list_val.remove(val_max)
        list_val_max.append(val_max)
    return list_val_max[-1]


""" corps du programme """

if __name__ == '__main__':
    mpl.use('QT5Agg')
    pathDB = path_database()
    start_T = time.time()
    dirpath = os.path.dirname(pathDB)
    dirname = os.path.basename(dirpath)
    freeze_support()
    nply = count_tables(pathDB)
    print("Chargement de la base de données...")
    load_clouds(pathDB, nply)
    print("Base de données chargée. (--- " + str(time.time() - start_T) + " secondes ---)")
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    form = MainWindow(pathDB)
    form.showMaximized()
    form.setWindowTitle(dirname)
    form.show()
    sys.exit(app.exec_())
