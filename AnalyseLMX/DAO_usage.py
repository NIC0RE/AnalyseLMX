# -*- coding: utf-8 -*-
import csv
import sqlite3

try:
    conn = sqlite3.connect("usage.db")
    cur = conn.cursor()
    print("Base de données est correctement connectée à SQLite")
    listdata=[]

    #sql = "SELECT sqlite_version();"
    sql = "select * from usage where id <= 10;"
    cur.execute(sql)
    res = cur.fetchall()
    #print("La version de SQLite est: ", res)
    for i in res:
        listdata.append(i)
    #print(res)
    print(listdata)
    cur.close()
    conn.close()
    print("La connexion SQLite est fermée")

except sqlite3.Error as error:
    print("Erreur lors de la connexion à SQLite", error)


with open('csvusage.csv', 'w', newline='') as csvusage:
    csvwriter = csv.writer(csvusage, delimiter=';',
                            quotechar=';', quoting=csv.QUOTE_MINIMAL)
    for i in listdata:
        csvwriter.writerow(i)



    