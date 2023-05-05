import argparse
import datetime
import csv
import sqlite3

def usage_evolution_licence():

    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--startdate",  help="The Start Date - format YYYY-MM-DD", required=True, type=datetime.date.fromisoformat)
    parser.add_argument("-e", "--enddate",  help="The End Date - format YYYY-MM-DD", required=True, type=datetime.date.fromisoformat)

    args = vars(parser.parse_args())

    startdate = args.get('startdate')
    enddate = args.get('enddate')
    #jour_debut = startdate.day
    jour_debut = startdate.strftime("%d")
    #mois_debut = startdate.month
    mois_debut = startdate.strftime("%m")
    #annee_debut = startdate.year
    annee_debut = startdate.strftime("%Y")
    #jour_fin = enddate.day
    jour_fin = enddate.strftime("%d")
    #mois_fin = enddate.month
    mois_fin = enddate.strftime("%m")
    #annee_fin = enddate.year
    annee_fin = enddate.strftime("%Y")


    try:
        database= "usage.db"
        conn = sqlite3.connect(database)
        cur = conn.cursor()
        print(database + " est correctement connectée à SQLite")
        listdata=[]
        sql = f"""select action, comment, SUBSTR(datetime(time, 'unixepoch', 'localtime'), 1, 10) as _t_, max(cast(SUBSTR(comment, INSTR( comment , 'COUNT:' )+6, 3) as integer)) as nb_token, 
        sum(cast(SUBSTR(comment, INSTR( comment , 'COUNT:' )+6, 3) as integer)) as total_token from usage where comment like '%FORGE3 %' and datetime(time, 'unixepoch', 'localtime') 
        between ('{annee_debut}-{mois_debut}-{jour_debut} 00:00:01') and ('{annee_fin}-{mois_fin}-{jour_fin} 23:59:59') group by _t_"""
        print(sql)
        cur.execute(sql)
        res = cur.fetchall()
        #print("La version de SQLite est: ", res)
        for i in res:
            listdata.append(i)
        print(res)
        #print(listdata)
        cur.close()
        conn.close()
        #print("La connexion SQLite est fermée")

    except sqlite3.Error as error:
        print("Erreur lors de la connexion à SQLite", error)

    col1="action"
    col2="comment"
    col3="date"
    col4="nombre_tokens_max"
    col5="nombre_token_total"

    with open('usage_évolution_licence.csv', 'w', newline='') as csv_évolution_licence:
        csvwriter = csv.writer(csv_évolution_licence, delimiter=';',
                                quotechar=';', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow([col1,col2,col3,col4,col5])
        for i in listdata:
            csvwriter.writerow(i)

if __name__ == "__main__":
    usage_evolution_licence()