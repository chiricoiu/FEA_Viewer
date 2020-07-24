# -*- coding:Utf8 -*-

__author__ = "Christian Hiricoiu"
__email__ = "christian.hiricoiu@gmail.com"

"""
Ce programme récupère en entrée 2 database créées par le programme '02_FEA-Post-Processing-Database-Generator':
Il récupère tous les plis et le noeuds de ces 2 programmes et fait la différence des deux.

Il récupère les données et les renvoie dans une database tierce qui est du même format que les 2 premières
"""

""" import externe """
import pandas as pd
import concurrent.futures
import tkinter as tk
from tkinter import filedialog
import time
import sqlite3

""" définition des fonctions """


def path_database():
    root = tk.Tk()
    root.withdraw()
    dbpath = filedialog.askopenfilename(title="Select database",
                                        parent=root,
                                        filetypes=[("Database Files", "*.db")])
    return dbpath


def count_tables(database_path):
    connector = sqlite3.connect(database_path)
    cursor = connector.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return len(cursor.fetchall())


def database_to_dataframe(database_path, nb_ply):
    dflist = []
    for ply in range(0, nb_ply):
        connector = sqlite3.connect(database_path)
        query = "SELECT * FROM Ply_" + str(ply + 1)
        df = pd.read_sql_query(query, connector)
        dflist.append(df)
    return dflist


def difference_dataframe(db_path1, db_path2, nb_ply):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(database_to_dataframe, db_path1, nb_ply)
        future2 = executor.submit(database_to_dataframe, db_path2, nb_ply)
    delta_df = []
    for p in range(0, nb_ply):
        delta_df.append([])
        df1 = future1.result()[p]
        df2 = future2.result()[p]
        for node in range(len(df1)):
            try:
                x = df1.x[node]
                y = df1.y[node]
                z = df1.z[node]
                if (x, y, z) == (df2.x[node], df2.y[node], df2.z[node]):
                    delta_vm = df1.Von_Mises[node] - df2.Von_Mises[node]
                    delta_disp = df1.displacement[node] - df2.displacement[node]
                    delta_th = df1.Tsai_Hill[node] - df2.Tsai_Hill[node]
                    delta_tw = df1.Tsai_Wu[node] - df2.Tsai_Wu[node]
                    delta_node = [x, y, z, delta_vm, delta_disp, delta_th, delta_tw]
                    delta_df[p].append(delta_node)
            except Exception as e:
                print(e)
    return delta_df


def data_dir():
    dialogbox = tk.Tk()
    dialogbox.withdraw()
    datadir = filedialog.askdirectory(title="select dir where you want to store database")
    return datadir


def create_database(datadir, nb_ply, listply):
    try:
        connector = sqlite3.connect(datadir + "/database_delta.db")
        cursor = connector.cursor()
        for numply in range(0, nb_ply):
            cursor.execute("CREATE TABLE Ply_" + str(numply + 1) +
                           " ([x] real, [y] real, [z] real, [Von_Mises] real, [displacement] real,"
                           " [Tsai_Hill] real, [Tsai_Wu] real)")
            for node in range(0, len(listply[numply])):
                table = "Ply_" + str(numply + 1)
                request = "INSERT INTO " + table + \
                          "(x,y,z,Von_Mises,displacement,Tsai_Hill,Tsai_Wu) VALUES(?,?,?,?,?,?,?)"
                cursor.execute(request, tuple(listply[numply][node]))
            pass
        pass
        connector.commit()
        connector.close()

    except NameError:
        print(NameError)


""" corps du programme """
if __name__ == '__main__':
    db_path_1 = path_database()
    db_path_2 = path_database()
    start_time = time.time()
    nbply = count_tables(db_path_1)
    delta = difference_dataframe(db_path_1, db_path_2, nbply)
    db_dir = data_dir()
    create_database(db_dir, int(nbply), delta)
    print("--- %s seconds (database)---" % (time.time() - start_time))
