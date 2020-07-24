# -*- coding:Utf8 -*-

__author__ = "Christian Hiricoiu"
__email__ = "christian.hiricoiu@gmail.com"

"""
Ce programme permet de calculer la masse du fuselage à partir des surfaces du modèle de calcul ainsi que des fichiers
contenant les drapages associées à ces surfaces.
"""

""" import externe """
import tkinter as tk
from tkinter import filedialog
import xlrd
import os
import pandas as pd
import time
import numpy as np
import pptk
import sqlite3

""" variables globales """

dirvar = ""  # variable qui gardera en mémoire le répertoire du fichier des drappages

""" définition des fonctions """


def charger_drapages():
    """ Sélection du fichier contenant les drapages """
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
        indexrepere = int(biblimeshsheet.cell_value(row, 1))
        indexstack = int(biblimeshsheet.cell_value(row, 2))
        booleanoffset = int(biblimeshsheet.cell_value(row, 3))
        booleancomposite = int(biblimeshsheet.cell_value(row, 4))
        listbiblimesh.append([zone, indexrepere, indexstack, booleanoffset, booleancomposite])
    return listbiblimesh


def charger_surfaces():
    """ Sélection du fichier contenant les aires des surfaces """
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    global dirvar
    surfaceareapath = filedialog.askopenfilename(initialdir=os.path.dirname(dirvar),
                                                 parent=dialogbox,
                                                 title="Select 'Surface Fuselage.xlsx'",
                                                 filetypes=[("Excel files", ".xlsx .xls")])
    surfaceareafile = xlrd.open_workbook(surfaceareapath, on_demand=True)
    surfaceareasheet = surfaceareafile.sheet_by_index(0)
    listsurfacearea = []
    for row in range(1, surfaceareasheet.nrows):
        numsurface = int(surfaceareasheet.cell_value(row, 0))
        surfacearea = surfaceareasheet.cell_value(row, 1)
        listsurfacearea.append([numsurface, surfacearea])
    return listsurfacearea


def import_data_meshsurf(filename):
    """ importation et lecture du txt """
    data = pd.read_csv(filename, sep="\t", header=2, index_col=False,
                       names=["x", "y", "z", "C1", "C2", "C3", "MeshPart"],
                       dtype=object,
                       low_memory=False)
    return data


def charger_data_meshsurf():
    """ Sélection du fichier contenant les centres des éléments du maillage"""
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    global dirvar
    datameshfilepath = filedialog.askopenfilename(initialdir=os.path.dirname(dirvar),
                                                  parent=dialogbox,
                                                  title="Select 'data_meshsurf.txt'",
                                                  filetypes=[("txt files", "*.txt")],)
    data = import_data_meshsurf(datameshfilepath)
    return data


def import_data_tw(filename):
    data = pd.read_csv(filename, sep="\t", header=1, index_col=False,
                       names=["x", "y", "z", "Tsai_Wu"],
                       low_memory=False)
    return data


def charger_data_tw():
    """ Sélection du fichier contenant les critères de Tsai-Wu"""
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    global dirvar
    datameshfilepath = filedialog.askopenfilename(initialdir=os.path.dirname(dirvar),
                                                  parent=dialogbox,
                                                  title="Select 'TsaiWu.txt'",
                                                  filetypes=[("txt files", "*.txt")])
    data = import_data_tw(datameshfilepath)
    return data


def mesh_surface(liststack, listbiblimesh, listsurfacearea):
    listmesh = []
    rho_t300, e_t300 = 1540, 0.23   # kg/m3, mm
    rho_t700, e_t700 = 1540, 0.42   # kg/m3, mm
    rho_t800, e_t800 = 1550, 0.3    # kg/m3, mm
    for surface in listsurfacearea:
        numero, aire = surface[0], round(float(surface[1]), 3)
        numstack = listbiblimesh[numero - 1][2]
        stack = liststack[numstack - 1]
        nb_t300, nb_t700, nb_t800, rho_mousse, e_mousse = 0, 0, 0, 0, 0
        for ply in stack:
            mat = ply[0]
            if mat == 'T300':
                nb_t300 += 1
            elif mat == 'T700':
                nb_t700 += 1
            elif mat == 'T800 UD':
                nb_t800 += 1
            else:
                mousse = mat.split()
                e_mousse = float(''.join(j for j in mousse[1] if j.isdigit()))
                rho_mousse = int(''.join(j for j in mousse[2] if j.isdigit()))
                print (rho_mousse, e_mousse)
        masse = round(aire * (rho_t300 * nb_t300 * e_t300 +
                              rho_t700 * nb_t700 * e_t700 +
                              rho_t800 * nb_t800 * e_t800 +
                              rho_mousse * e_mousse) / 1000, 3)
        listmesh.append([numero, aire, masse])
    return listmesh


def tsaiwudf(dftw):
    listtw = []
    for node in range(dftw.shape[0]):
        x = dftw.x[node]
        y = dftw.y[node]
        z = dftw.z[node]
        tw = dftw.Tsai_Wu[node]
        listtw.append([x, y, z, tw])
    return listtw


def meshdf(dfms):
    xyz_list, listmesh = [], []
    for node in range(dfms.shape[0]):
        x = dfms.x[node]
        y = dfms.y[node]
        z = dfms.z[node]
        meshpart = dfms.MeshPart[node]
        xyz_node = [x, y, z]
        if xyz_node not in xyz_list:
            xyz_list.append(xyz_node)
            element_to_add = xyz_node.copy()
            element_to_add.append(meshpart)
            listmesh.append(element_to_add)
    return listmesh


def joindata(dfsurface, dftw, dfmesh):
    df = []
    for mesh_node in dfmesh:
        numero_surface = mesh_node[3]
        for surface in dfsurface:
            if surface[0] == numero_surface:
                aire, masse = surface[1], surface[2]
                mesh_node.append(masse)
                mesh_node.append(aire)
        for tw_node in dftw:
            if tw_node[0] == mesh_node[0] and tw_node[1] == mesh_node[1] and tw_node[2] == mesh_node[2]:
                tw = tw_node[3]
                mesh_node.append(tw)
        df.append(mesh_node)
    return df


def data_dir():
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    datadir = filedialog.askdirectory(title="select directory where database will be stored.")
    return datadir


def create_database(datadir, df):
    try:
        connector = sqlite3.connect(datadir + "/database.db")
        cursor = connector.cursor()
        cursor.execute("CREATE TABLE Data ([x] real, [y] real, [z] real, [Mesh] int, [Aire] real, [Mass] real, "
                       "[TsaiWu] real)")
        for node in df:
            request = "INSERT INTO Data (x,y,z,Mesh,Aire,Masse,Tsai_Wu) VALUES(?,?,?,?,?,?,?)"
            cursor.execute(request, tuple(node))
        connector.commit()
        connector.close()
    except Exception as e:
        print(e)


""" corps du programme """
if __name__ == '__main__':
    Liststack = charger_drapages()
    ListBibli = charger_bibli()
    ListSurf = charger_surfaces()

    start = time.time()
    List_Aire_Masse = mesh_surface(Liststack, ListBibli, ListSurf)
    print("List_Aire_Masse : ", time.time() - start, " (s)")
    print(List_Aire_Masse)
    
    masse_modif = 0
    surface_modif = 0
    masse_fuselage = 0
    
    list_modif = [1232]
    
    for surface in List_Aire_Masse:     # surface=[numero,aire,masse] 
        if surface[0] in list_modif:
            surface_modif = surface_modif + surface[1]
    print("L'aire des surfaces modifiées est", surface_modif, " m²")  
    
    for surface in List_Aire_Masse:     # surface=[numero,aire,masse] 
        if surface[0] in list_modif:
            masse_modif = masse_modif + surface[2]
    print("La masse des surfaces modifiées est", masse_modif, " kg")
    
    for surface in List_Aire_Masse:     # surface=[numero,aire,masse] 
        masse_fuselage = masse_fuselage + surface[2]
    print("La masse du fuselage (rho = 1540 kg/m3) est", masse_fuselage, " kg")
    
    a = input("appuyez sur une touche pour fermer le programme...")


