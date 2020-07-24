# -*- coding:Utf8 -*-

__author__ = "Christian Hiricoiu"
__email__ = "christian.hiricoiu@gmail.com"

"""
Ce programme permet de générer un mapping file pour le fuselage du P51.
Il permet d'affecter des propriétés composites dans le module 'Analysis' de CATIA sans avoir à rentrer "à la main" les
propriétés via le module 'composites design'.

Ce programme utilise en entrée 3 feuilles excel et 1 fichier txt :
Stackings.xls - Ce fichier contient les différents types de drappages existant dans la structure composite du modèle.
     Axis.xls - Ce fichier contient les différents systèmes d'axes utilisés pour définir les directions de drappage.
   Biblio.xls - Ce fichier associe à chaque surface maillée du modèle CATIA un drappage et un système d'axes définis 
                dans les 2 feuilles excel précédentes.
     data.txt - Ce fichier est extrait de Catia via le module "Analysis", il contient le centre de chaque maille.
"""

""" import externe """

import os
import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as et
import numpy as np
import xlrd
import pandas as pd
import time

""" variables globales """

dirvar = ""  # variable qui gardera en mémoire le répertoire du fichier des drappages

""" définition des fonctions """


def charger_drappages():
    """ Sélection du fichier contenant les drappages """
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    sheetpath = filedialog.askopenfilename(initialdir="/",
                                           parent=dialogbox,
                                           title="Select 'Stackings.xlsx'",
                                           filetypes=[("Excel files", ".xlsx .xls")])
    global dirvar
    dirvar = sheetpath
    stackfile = xlrd.open_workbook(sheetpath, on_demand=True)
    nbstack = len(stackfile.sheet_names())
    liststack = []
    for i in range(0, nbstack):
        stacksheet = stackfile.sheet_by_index(i)
        liststack.append([])
        for row in range(1, stacksheet.nrows):
            mat = stacksheet.cell_value(row, 0)
            th = stacksheet.cell_value(row, 1)
            angle = stacksheet.cell_value(row, 2)
            pos = int(stacksheet.cell_value(row, 3))
            liststack[i].append([str(mat), str(th), str(angle), str(pos)])
    return liststack


def charger_axes():
    """ Sélection du fichier contenant les systèmes d'axes """
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    global dirvar
    axispath = filedialog.askopenfilename(initialdir=os.path.dirname(dirvar),
                                          parent=dialogbox,
                                          title="Select 'Axis.xlsx'",
                                          filetypes=[("Excel files", ".xlsx .xls")])
    axisfile = xlrd.open_workbook(axispath, on_demand=True)
    axissheet = axisfile.sheet_by_index(0)
    listaxis = []
    for row in range(1, axissheet.nrows):
        cood_o = axissheet.cell_value(row, 0)
        coord_x = axissheet.cell_value(row, 1)
        coord_y = axissheet.cell_value(row, 2)
        listaxis.append(str(cood_o) + ";" + str(coord_x) + ";" + str(coord_y))
    return listaxis


def charger_bibli():
    """ Sélection du fichier d'association des surfaces maillées aux propriétés composites """
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    global dirvar
    biblimeshpath = filedialog.askopenfilename(initialdir=os.path.dirname(dirvar),
                                               parent=dialogbox,
                                               title="Select 'biblimesh.xlsx'",
                                               filetypes=[("Excel files", ".xlsx .xls")])
    biblimeshfile = xlrd.open_workbook(biblimeshpath, on_demand=True)
    biblimeshsheet = biblimeshfile.sheet_by_index(0)
    listbiblimesh = []
    for row in range(1, biblimeshsheet.nrows):
        zone = int(biblimeshsheet.cell_value(row, 0))
        indexstack = int(biblimeshsheet.cell_value(row, 1))
        indexrepere = int(biblimeshsheet.cell_value(row, 2))
        booleanoffset = int(biblimeshsheet.cell_value(row, 3))
        booleancomposite = int(biblimeshsheet.cell_value(row, 4))
        listbiblimesh.append([zone, indexstack, indexrepere, booleanoffset, booleancomposite])
    return listbiblimesh


def charger_data_centroid():
    """ Sélection du fichier contenant les centres des éléments du maillage"""
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    global dirvar
    datameshfilepath = filedialog.askopenfilename(initialdir=os.path.dirname(dirvar),
                                                  parent=dialogbox,
                                                  title="Select CATIA 'data.txt'",
                                                  filetypes=[("txt files", "*.txt")])
    data = import_data_centroid(datameshfilepath)
    return data


def import_data_centroid(filename):
    """ importation et lecture du txt """
    data = pd.read_csv(filename, sep="\t", header=2, index_col=False,
                       names=["x", "y", "z", "C1", "C2", "C3", "MeshPart"], dtype=object)
    return data


def ecriture_mapping_file(liststacking, listaxis, listbiblimesh, data):
    """ Ecriture du MappingFile.xml à partir de toutes les data récupérées """
    ns = 'http://www.w3.org/2001/XMLSchema-instance'
    location_attribute = '{%s}noNamespaceSchemaLocation' % ns
    root = et.Element('ListOfProperties', attrib={location_attribute: 'PropertyMappingRules.xsd'})
    defaultvaluesnode = et.SubElement(root, 'DEFAULT_VALUES', AXIS="0;0;0;1;0;0;0;1;0", TOL="1")
    unitsnode = et.SubElement(root, 'UNITS', ANGLE="deg", LENGTH="mm")
    time_start = time.time()
    print("Le fichier 'mappingfile.xml' est en cours d'écriture... Patience !")
    for i in range(0, data.shape[0]):

        indexmesh = int(''.join(j for j in data.MeshPart[i] if j.isdigit()))
        index_a = listbiblimesh[indexmesh - 1][1] - 1
        index_s = listbiblimesh[indexmesh - 1][2] - 1
        booleanoffset = listbiblimesh[indexmesh - 1][3]
        booleancomposite = listbiblimesh[indexmesh - 1][4]

        axis = listaxis[index_a]
        x = data.x[i]
        y = data.y[i]
        z = data.z[i]

        matrixoffset = np.array(liststacking[index_s])
        matrixoffset = matrixoffset[:, 1].astype('float64')
        thickness = sum(matrixoffset)
        if booleancomposite == 1:
            if booleanoffset == 1:
                shellnode = et.SubElement(root, 'COMPOSITE_SHELL',
                                          COMPOSITE_AXIS=axis,
                                          BELONG_TO_MP=data.MeshPart[i],
                                          X=x, Y=y, Z=z,
                                          SURFACE_OFFSET=str(thickness / 2))
                for ply in range(0, len(liststacking[index_s])):
                    laminanode = et.SubElement(shellnode, 'LAMINA',
                                               MAT=liststacking[index_s][ply][0],
                                               TH=liststacking[index_s][ply][1],
                                               ANGLE=liststacking[index_s][ply][2],
                                               POSITION=liststacking[index_s][ply][3])
            elif booleanoffset == 0:
                shellnode = et.SubElement(root, 'COMPOSITE_SHELL',
                                          COMPOSITE_AXIS=axis,
                                          BELONG_TO_MP=data.MeshPart[i],
                                          X=x, Y=y, Z=z,
                                          )
                for ply in range(0, len(liststacking[index_s])):
                    laminanode = et.SubElement(shellnode, 'LAMINA',
                                               MAT=liststacking[index_s][ply][0],
                                               TH=liststacking[index_s][ply][1],
                                               ANGLE=liststacking[index_s][ply][2],
                                               POSITION=liststacking[index_s][ply][3])
        elif booleancomposite == 0:
            shellnode = et.SubElement(root, 'SHELL',
                                      BELONG_TO_MP=data.MeshPart[i],
                                      X=x, Y=y, Z=z,
                                      TH="30", MAT="Plexiglass")
    print("Le fichier est généré (--- %s secondes ---)" % (time.time() - time_start))
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    global dirvar
    mappingfilepath = filedialog.askdirectory(initialdir=os.path.dirname(dirvar),
                                              parent=dialogbox,
                                              title="Select the directory for 'MappingFile.xml'")

    tree = et.ElementTree(root)
    tree.write(mappingfilepath + "/MappingFile.xml", xml_declaration=True, encoding='utf-8')


""" corps du programme """
if __name__ == '__main__':
    try:
        lstack = charger_drappages()
        laxis = charger_axes()
        lbibli = charger_bibli()
        datacentr = charger_data_centroid()
        ecriture_mapping_file(lstack, laxis, lbibli, datacentr)
    except Exception as e:
        print(e)
