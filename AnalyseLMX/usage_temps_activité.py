import argparse
import datetime
import csv
import sqlite3

def usage_temps_activite():

    try:
        database= "usage.db"
        conn = sqlite3.connect(database)
        cur = conn.cursor()
        print(database + " est correctement connectée à SQLite")
        liststartup=[]
        listshutdown=[]
        startupquery = f"""select datetime(time, 'unixepoch', 'localtime') as date_depart from usage where action = 'STARTUP'"""
        print(startupquery)
        cur.execute(startupquery)
        res1 = cur.fetchall()
        for i in res1:
            liststartup.append(i)
        shutdownquery = f"""select datetime(time, 'unixepoch', 'localtime') as date_fin from usage where action = 'SHUTDOWN'"""
        print(shutdownquery)
        cur.execute(shutdownquery)
        res2 = cur.fetchall()
        for i in res2:
            listshutdown.append(i)
        cur.close()
        conn.close()

    except sqlite3.Error as error:
        print("Erreur lors de la connexion à SQLite", error)

    col1="date_depart"
    col2="date_arrêt"
    col3="date_diff (temps d'activité)"

    with open('usage_temps_activité.csv', 'w', newline='') as csv_temps_activité:
        csvwriter = csv.writer(csv_temps_activité, delimiter=';',
                                quotechar=';', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow([col1,col2,col3])
        for i in range (len(listshutdown)):
            date_str1= str(liststartup[i])[2:21]
            date_str2= str(listshutdown[i])[2:21]
            date_diff= datetime.datetime.strptime(date_str2, '%Y-%m-%d %H:%M:%S')-datetime.datetime.strptime(date_str1, '%Y-%m-%d %H:%M:%S')
            csvwriter.writerow([date_str1, date_str2, date_diff])


if __name__ == "__main__":
    usage_temps_activite()