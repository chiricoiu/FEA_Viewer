# -*- coding:Utf8 -*-

__author__ = "Christian Hiricoiu"
__email__ = "christian.hiricoiu@gmail.com"

"""
Ce programme génère un fichier base de données .db contenant les résultats de calcul générés par CATIA. 

Il prend en entrée le dossier où sont stockés les .txt contenant les valeurs des critères de Von Mises, Tsai Hill, Tsai 
Wu ainsi que les déplacements.
"""

""" import externe """
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
import sqlite3
import time
import concurrent.futures

""" définition des fonctions """


def import_data_vm(filename):
    data = pd.read_csv(filename, sep="\t", header=1, index_col=False,
                       names=["x", "y", "z", "Von_Mises"])
    return data


def import_data_disp(filename):
    data = pd.read_csv(filename, sep="\t", header=1, index_col=False,
                       names=["x", "y", "z", "Displacement"])
    return data


def import_data_th(filename):
    data = pd.read_csv(filename, sep="\t", header=2, index_col=False,
                       names=["x", "y", "z", "Tsai_Hill"])
    return data


def import_data_tw(filename):
    data = pd.read_csv(filename, sep="\t", header=2, index_col=False,
                       names=["x", "y", "z", "Tsai_Wu"])
    return data


def data_dir():
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    datadir = filedialog.askdirectory(title="select directory where all datas are stored.")
    return datadir


def ply_count(datadir):
    subdir = datadir + "/Von Mises"
    nbply = os.listdir(subdir)
    return len(nbply)


def txtfile_import(datadir, nbply):
    list_df_vm, list_df_th, list_df_tw, list_df_disp, = [], [], [], []

    for numply in range(0, nbply):
        list_df_vm.append(import_data_vm(datadir + "/Von Mises/Data_VonMises_" + str(numply + 1) + ".txt"))
        list_df_th.append(import_data_th(datadir + "/Tsai Hill/Data_TsaiHill_" + str(numply + 1) + ".txt"))
        list_df_tw.append(import_data_tw(datadir + "/Tsai Wu/Data_TsaiWu_" + str(numply + 1) + ".txt"))
        pass
    list_df_disp.append(import_data_disp(datadir + "/Data_Displacement.txt"))
    df = [list_df_vm, list_df_th, list_df_tw, list_df_disp]
    return df


def coord_nodes_and_vm_val(df, nbply):
    list_coord = []
    list_vm_val = []
    crit = 0
    for numply in range(nbply):
        print("ajout ply " + str(numply + 1) + " von_mises")
        list_coord.append([])
        list_vm_val.append([])
        for node in range(0, len(df[crit][numply])):
            x = df[crit][numply].x[node]
            y = df[crit][numply].y[node]
            z = df[crit][numply].z[node]
            vonmises_val = df[crit][numply].Von_Mises[node]
            list_coord[numply].append([x, y, z])
            list_vm_val[numply].append(vonmises_val)
    return list_coord, list_vm_val


def tsaihill_val(df, list_coord, nbply):
    list_th_val = []
    crit = 1
    for numply in range(nbply):
        print("ajout ply " + str(numply + 1) + " tsai_hill")
        list_th_val.append([])
        i_th = 0
        for node in range(0, len(df[0][numply])):
            try:
                x = list_coord[numply][node][0]
                y = list_coord[numply][node][1]
                z = list_coord[numply][node][2]
                if (df[crit][numply].x[i_th] == x) & (df[crit][numply].y[i_th] == y) & (df[crit][numply].z[i_th] == z):
                    th_val = df[crit][numply].Tsai_Hill[i_th]
                    i_th += 1
                else:
                    index_th = df[crit][numply].loc[(df[crit][numply]['x'] == x) &
                                                    (df[crit][numply]['y'] == y) &
                                                    (df[crit][numply]['z'] == z)].index[0]
                    th_val = df[crit][numply].Tsai_Hill[index_th]
                    i_th = index_th + 1
                list_th_val[numply].append(th_val)
            except Exception as e:
                print(e)
    return list_th_val


def tsaiwu_val(df, list_coord, nbply):
    list_tw_val = []
    crit = 2
    for numply in range(nbply):
        print("ajout ply " + str(numply + 1) + " tsai_wu")
        list_tw_val.append([])
        i_tw = 0
        for node in range(0, len(df[0][numply])):
            try:
                x = list_coord[numply][node][0]
                y = list_coord[numply][node][1]
                z = list_coord[numply][node][2]
                if (df[crit][numply].x[i_tw] == x) & (df[crit][numply].y[i_tw] == y) & (df[crit][numply].z[i_tw] == z):
                    tsaiwuvalue = df[crit][numply].Tsai_Wu[i_tw]
                    i_tw += 1
                else:
                    index_tw = df[crit][numply].loc[(df[crit][numply]['x'] == x) &
                                                    (df[crit][numply]['y'] == y) &
                                                    (df[crit][numply]['z'] == z)].index[0]
                    tsaiwuvalue = df[crit][numply].Tsai_Wu[index_tw]
                    i_tw = index_tw + 1
                list_tw_val[numply].append(tsaiwuvalue)
            except Exception as e:
                print(e)
    return list_tw_val


def displacement_val(df, list_coord):
    list_disp_val = []
    crit = 3
    i_de = 0
    for node in range(0, len(df[0][0])):
        try:
            x = list_coord[0][node][0]
            y = list_coord[0][node][1]
            z = list_coord[0][node][2]
            if (df[crit][0].x[i_de] == x) & (df[crit][0].y[i_de] == y) & (df[crit][0].z[i_de] == z):
                dispvalue = df[crit][0].Displacement[i_de]
                i_de += 1
            else:
                index_disp = df[crit].loc[(df[crit]['x'] == x) &
                                          (df[crit]['y'] == y) &
                                          (df[crit]['z'] == z)].index[0]
                dispvalue = df[crit][0].Displacement[index_disp]
                i_de = index_disp + 1
            list_disp_val.append(dispvalue)
        except Exception as e:
            print(e)
    return list_disp_val


def join_val(list_coord, vm_val, th_val, tw_val, disp_val):
    list_val = []
    for ply in range(0, len(list_coord)):
        list_val.append([])
        for node in range(0, len(list_coord[ply])):
            try:
                x = list_coord[ply][node][0]
                y = list_coord[ply][node][1]
                z = list_coord[ply][node][2]
                tsaihill = th_val[ply][node]
                tsaiwu = tw_val[ply][node]
                vonmises = vm_val[ply][node]
                displacement = disp_val[node]
                node_value = [x, y, z, tsaihill, tsaiwu, vonmises, displacement]
                list_val[ply].append(node_value)
            except Exception as e:
                print(e)
    return list_val


def create_database(datadir, nbply, listply):
    try:
        connector = sqlite3.connect(datadir + "/database.db")
        cursor = connector.cursor()
        for numply in range(0, nbply):
            cursor.execute("CREATE TABLE Ply_" + str(numply + 1) +
                           " ([x] real, [y] real, [z] real, [Tsai_Hill] real, [Tsai_Wu] real,"
                           " [Von_Mises] real, [displacement] real)")
            for node in range(0, len(listply[numply])):
                table = "Ply_" + str(numply + 1)
                request = "INSERT INTO " + table + \
                          "(x,y,z,Tsai_Hill,Tsai_Wu,Von_Mises,displacement) VALUES(?,?,?,?,?,?,?)"
                cursor.execute(request, tuple(listply[numply][node]))
        connector.commit()
        connector.close()
    except Exception as e:
        print(e)


""" corps du programme """
if __name__ == '__main__':
    maindir = data_dir()
    print("Répertoire de la base de données : \n '" + maindir + "'")
    start_time = time.time()
    Nbply = ply_count(maindir)
    Dflist = txtfile_import(maindir, Nbply)
    coordinates_xyz, vonmises_nodes = coord_nodes_and_vm_val(Dflist, Nbply)
    print("database en cours de création... Patience")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(tsaihill_val, Dflist, coordinates_xyz, Nbply)
        future2 = executor.submit(tsaiwu_val, Dflist, coordinates_xyz, Nbply)
        future3 = executor.submit(displacement_val, Dflist, coordinates_xyz)
    Dfsorted = join_val(coordinates_xyz, vonmises_nodes, future1.result(), future2.result(), future3.result())
    create_database(maindir, Nbply, Dfsorted)
    print("database enregistrée !")
    print("--- program duration : %s seconds ---" % (time.time() - start_time))
