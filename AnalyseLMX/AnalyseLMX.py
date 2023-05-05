import argparse
import datetime
from datetime import timedelta
import csv
import sqlite3
import os


parser = argparse.ArgumentParser()

parser.add_argument("-s", "--startdate",  help="The Start Date - format YYYY-MM-DD", required=True, type=datetime.date.fromisoformat)
parser.add_argument("-e", "--enddate",  help="The End Date - format YYYY-MM-DD", required=True, type=datetime.date.fromisoformat)
parser.add_argument("-a", "--analysis",  help="The Chosen Analysis - Check the doc if you don't know what to type", required=True, type=str)

try:
    args = vars(parser.parse_args())
    startdate = args.get('startdate')
    enddate = args.get('enddate')
    analysis = args.get('analysis')
except:
    startdate = datetime.date.fromisoformat(input("Saisir la date de départ (Format : YYYY-MM-DD) : "))
    enddate = datetime.date.fromisoformat(input("Saisir la date de fin (Format : YYYY-MM-DD) : "))
    analysis = input("Saisir l'analyse (The Chosen Analysis - Check the doc if you don't know what to type): ")

jour_debut = startdate.strftime("%d")

mois_debut = startdate.strftime("%m")

annee_debut = startdate.strftime("%Y")

jour_fin = enddate.strftime("%d")

mois_fin = enddate.strftime("%m")

annee_fin = enddate.strftime("%Y")

"""-----------------------------------------------------------------------------USAGE_TEMPS_ACTIVITE-------------------------------------------------------------------------------------------------"""
def usage_temps_activite():
    try:
        database= "usage.db"
        conn = sqlite3.connect(database)
        cur = conn.cursor()
        print(database + " est correctement connectée à SQLite")
        liststartup=[]
        listshutdown=[]
        startupquery = f"""select datetime(time, 'unixepoch', 'localtime') as date_depart from usage where action = 'STARTUP'"""
        cur.execute(startupquery)
        res1 = cur.fetchall()
        for i in res1:
            liststartup.append(i)
        shutdownquery = f"""select datetime(time, 'unixepoch', 'localtime') as date_fin from usage where action = 'SHUTDOWN'"""
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
    
    print("Les données ont été ajoutées au fichier usage_temps_activité.csv")


"""-----------------------------------------------------------------------------USAGE_EVOLUTION_LICENCE-------------------------------------------------------------------------------------------------"""
def usage_evolution_licence():

    try:
        database= "usage.db"
        conn = sqlite3.connect(database)
        cur = conn.cursor()
        print(database + " est correctement connectée à SQLite")
        listdata=[]
        sql = f"""select action, comment, SUBSTR(datetime(time, 'unixepoch', 'localtime'), 1, 10) as _t_, max(cast(SUBSTR(comment, INSTR( comment , 'COUNT:' )+6, 3) as integer)) as nb_token, 
        sum(cast(SUBSTR(comment, INSTR( comment , 'COUNT:' )+6, 3) as integer)) as total_token from usage where comment like '%FORGE3 %' and datetime(time, 'unixepoch', 'localtime') 
        between ('{annee_debut}-{mois_debut}-{jour_debut} 00:00:01') and ('{annee_fin}-{mois_fin}-{jour_fin} 23:59:59') group by _t_"""
        cur.execute(sql)
        res = cur.fetchall()
        for i in res:
            listdata.append(i)
        cur.close()
        conn.close()

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
    
    print("Les données ont été ajoutées au fichier usage_évolution_licence.csv")


"""-----------------------------------------------------------------------------USAGE_AGREGAT_CHECKOUT-------------------------------------------------------------------------------------------------"""


class Calcul:

    """This is a Calcul object. 
    It will group records that have the same action and features and are close enough in time.

    :param int id: The object ID. Not to be confused with the record ID though !
    :param string feature: The object feature. Every record in the object has the same.
    :param int tokens: The total number of tokens contained in the object. For each (checkout) record in the object, the token count goes up by a certain amount.
    :param int nbdate: Number of checkout dates stored in the object.
    :param list groupedate: A list that contains all of the records dates. At first it's just the checkout ones, but it will also take the checkin dates if one or more are linked to the object.
    :param list groupedate: A list that contains all of the records IDs. At first it's just the checkout ones, but it will also take the checkin IDs if one or more are linked to the object.
    :param int alradded: It stands for "already added". When an object is instantiated it's value is 0. But when a checkin object is linked to it, it takes the value 1.
    """

    def __init__(self, id):
        """The constructor."""
        self.id = id #L'ID du calcul (et pas de l'enregistrement)
        self.feature = "" #Feature (passage parsé du champs comment)
        self.tokens = 0 #Nombre de token total du calcul
        self.nbdate = 0 #Nombre de dates de checkout
        self.groupedate = []    #Répertorie toutes les dates sur lesquelles le calcul s'est fait
        self.groupeid = []      #Répertorie tous les ID des enregistrement qui font partie du même calcul
        self.alradded = 0 #Par défaut à 0, puis à 1 lorsque la liaison avec un checkin s'effectue 

    def add_to_groupdate(self, groupdate):
        """Simply adds a chosen date in the groupedate list.

        :param date groupdate: A date to add in the list.
        """
        self.groupedate.append(groupdate)   #Méthode qui ajoute une date à la liste de dates du calcul
    
    def add_to_groupid(self, groupid):  
        """Simply adds the ID of the chosen record in the groupeid list.

        :param date groupid: An ID to add in the list.
        """
        self.groupeid.append(groupid)   #Méthode qui ajoute un ID à la liste d'ID du calcul

class index:

    """This is an index object. 
    It serves as an object indicator by giving them an index. Since objects navigate and group thousands of records, it is easier to locate them.

    :param int indexid: The indexid is nothing but an ID. It's convenient for numbering Calcul objects.
    """

    def __init__(self, indexid):
        self.indexid = indexid #L'ID du calcul (et pas de l'enregistrement)

def agregat_checkout(date_demarrage,date_arret,index):
    #global indexid
    date_demarrage=datetime.datetime.strptime(date_demarrage, '%Y-%m-%d %H:%M:%S')
    date_arret=datetime.datetime.strptime(date_arret, '%Y-%m-%d %H:%M:%S')
    try:
        database= "usage.db"
        conn = sqlite3.connect(database)
        cur = conn.cursor()
        print(database + " est correctement connectée à SQLite")
        listcheck=[]
        listfeature=[]
        listfeatureCO=[]
        listfeatureCI=[]
        
        """-------------------------------------------------------------------------------REQUETES------------------------------------------------------------------------------------------------"""
        
        print("Les requêtes sont lancées.")
        print("enregistrements entre: "+str(date_demarrage)+" et "+str(date_arret))
        checkquery = f"""select action, datetime(time, 'unixepoch', 'localtime') as _t_, id, SUBSTR(comment, 10, (INSTR( comment , ' U' )-INSTR(comment, ':')-1)) as feature, 
    cast(SUBSTR(comment, INSTR( comment , 'COUNT:' )+6, 3) as integer) as nb_token from usage where (action = 'CHECKOUT' or action='CHECKIN') and (_t_ between '{date_demarrage}' and '{date_arret}')"""
        cur.execute(checkquery)
        res5 = cur.fetchall()
        for i in res5:
            listcheck.append(i)
        featurequery = f"""select datetime(time, 'unixepoch', 'localtime') as _t_, SUBSTR(comment, 10, (INSTR( comment , ' U' )-INSTR(comment, ':')-1)) as feature, 
        count(id) from usage where (action = 'CHECKOUT' or action='CHECKIN') and (_t_ between '{date_demarrage}' and '{date_arret}') group by feature"""
        cur.execute(featurequery)
        res6 = cur.fetchall()
        for i in res6:
            listfeature.append(i)
        featurequeryCO = f"""select datetime(time, 'unixepoch', 'localtime') as _t_, SUBSTR(comment, 10, (INSTR( comment , ' U' )-INSTR(comment, ':')-1)) as feature, 
    count(id) from usage where action = 'CHECKOUT' and (_t_ between '{date_demarrage}' and '{date_arret}') group by feature"""
        cur.execute(featurequeryCO)
        res7 = cur.fetchall()
        for i in res7:
            listfeatureCO.append(i)
        featurequeryCI = f"""select datetime(time, 'unixepoch', 'localtime') as _t_, SUBSTR(comment, 10, (INSTR( comment , ' U' )-INSTR(comment, ':')-1)) as feature, 
    count(id) from usage where action = 'CHECKIN' and (_t_ between '{date_demarrage}' and '{date_arret}') group by feature"""
        cur.execute(featurequeryCI)
        res8 = cur.fetchall()
        for i in res8:
            listfeatureCI.append(i)
        

    except sqlite3.Error as error:
        print("Erreur lors de la connexion à SQLite", error)     
    

    """-------------------------------------------Boucle principale-------------------------------------------"""
    
    countfeature=0
    countfeature2=-1
    quierofeature=[] 
    idcheckin=[]    #Liste qui contient tous les id des enregistrements avec des actions checkin
    listobject=[]   #Liste qui regroupe tous les objets de la première boucle (les checkout)
    listobject2=[]  #Liste qui regroupe tous les objets de la deuxième boucle (les checkin)
    listcheckin=[]  #Liste dans laquelle on ajoute les OBJETS avec une action checkin lors du parcours de la première boucle, on s'en sert plus tard 
    listcheckin2=[] #Liste dans laquelle on ajoute les ENREGISTREMENTS avec une action checkin lors du parcours de la première boucle, on s'en sert pour la deuxième boucle
    delay=["0:00:00","0:00:01","0:00:02","0:00:03","0:00:04","0:00:05","0:00:06",
    "0:00:07","0:00:08","0:00:09","0:00:10"]    #Liste qui contient les délais possibles de 1 à 10s, on comparera les résultats de soustraction de date avec les valeurs contenues dans cette liste  
    dateact=date_demarrage   #On initialise la date actuelle (utilisée dans la fonction pour vérifier les délais) à la date indiquée par l'utilisateur
    if len(listcheck) > 0:    
        obj = Calcul(index.indexid)
        objprecedent= obj
        countcheckin=0
        countcheckout=0 #On compte le nombre de checkin et de checkout pour se faire une idée du nombre d'enregistrement attendu
        print(len(listcheck))
        while countfeature < len(listfeature):  #Tant que countfeature n'est pas égal à la longueur de listfeature, c'est que les enregistrements avec une ou plusieurs feature de listfeature n'ont pas été récupérées
            wantedfeature=listfeature[countfeature][1]  #L'idée va être de parcourir la listcheck à la recherche des enregistrement qui possède une feature en particulier (qui change à chaque tour de boucle)
            for p in listfeatureCO:
                if p[1]==wantedfeature:
                    countfeature2+=1
            quierofeature.append(wantedfeature)
            featurecomplete=0
            k=0
            while k < len(listcheck):   #On va parcourir la listcheck dans son entièreté mais avec un while
                action = listcheck[k][0]
                date = listcheck[k][1]
                id = listcheck[k][2]        #On initialise les variables qu'on voudra afficher plus tard. 
                feature = listcheck[k][3]   #Les champs importants correspondent aux indices 0,1,2,3,4 de chaque enregistrement (c'est l'ordre qui a été determiné dans la requête SQL)
                nb_token = listcheck[k][4]
                if action == "CHECKOUT": 
                    if feature == wantedfeature: #Si la feature est bien celle souhaitée
                        if str(datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S') - dateact) in delay : #Si le délai est inférieur à 10s (on fait la soustraction de la date actuelle et de la date de l'enregistrement)
                            if date not in obj.groupedate:
                                obj.add_to_groupdate(date)  #On ajoute la date à la liste de date de l'objet actuel si elle n'y est pas déjà
                                obj.nbdate+=1
                            obj.add_to_groupid(id)  #Dans tous les cas, on ajoute l'id à la liste d'id de l'objet actuel (car il ne peut pas déjà y être)
                            obj.tokens += nb_token  #On ajoute le nombre de token de l'enregistrement à ceux de l'objet
                            obj.feature = feature   #Pour le premier tour de boucle qui arrive jusqu'ici, on indique que la feature de l'objet est celle de l'enregistrement
                            featurecomplete+=1
                            if str(featurecomplete)==str(listfeatureCO[countfeature2][2]):
                                listobject.append(objprecedent)
                                index.indexid+=1
                                obj = Calcul(index.indexid)
                        else:
                            if objprecedent.groupeid:
                                listobject.append(objprecedent) #Si le délai de 10s est dépassé on ajoute l'objet précédant à la liste d'objet 
                                index.indexid+=1
                            if index.indexid==9071:
                                print(objprecedent.groupeid)
                                print(objprecedent.groupedate)
                                print(obj.groupeid)
                                print(obj.groupedate)
                            obj = Calcul(index.indexid)   #Et on passe à un nouvel objet
                            dateact = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S') #Il faut donc indiquer que la nouvelle date à comparer est celle de ce nouvel objet
                            if date not in obj.groupedate:
                                obj.add_to_groupdate(date)
                                obj.nbdate+=1
                            obj.add_to_groupid(id)
                            obj.tokens += nb_token  #Puisque c'est la première instance d'un nouvel objet, on ajoute directement les champs date, id, nombre de token, et feature à ce nouvel objet
                            obj.feature = feature   #On en aura besoin pour faire la comparaison avec les enregistrements suivants  
                    else:
                        k+=1
                        continue    #On passe au tour de boucle suivant directement
                else:
                    if id not in idcheckin:
                        listcheckin.append(obj) #Si l'action est un checkin au lieu d'un checkout on ajoute cet objet à une liste d'objets consacrée aux checkin
                        listcheckin2.append(listcheck[k])   #On ajoute aussi l'enregistrement actuel à une liste d'enegistrements consacrée aux checkin
                    idcheckin.append(id)
                    countcheckin+=1
                    k+=1
                    continue    #On passe au tour de boucle suivant directement
                k+=1    
                objprecedent=obj 
                countcheckout+=1
            dateact = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            countfeature+=1
        listobject.append(objprecedent)
        print(objprecedent.groupeid)
        print(objprecedent.groupedate)
        print(obj.groupeid)
        print(obj.groupedate)
        print(index.indexid)

    
        """---------CSV 1--------"""

        with open('usage_tri_checkout.csv', 'a', newline='') as csv_tri_checkout:
            csvwriter = csv.writer(csv_tri_checkout, delimiter=';',
                                    quotechar=';', quoting=csv.QUOTE_MINIMAL)
            objectbefore=Calcul(0)
            for object in listobject:
                if object.id == objectbefore.id and object.feature == objectbefore.feature and object.tokens == objectbefore.tokens and object.groupeid == objectbefore.groupeid and object.groupedate == objectbefore.groupedate :
                    continue
                else:
                    csvwriter.writerow([object.id, object.feature, object.tokens, object.groupeid, object.groupedate])
                    objectbefore = object
                
    else:
        index.indexid-=1

    """-------------------------------------------Boucle pour les CHECKIN-------------------------------------------"""

    if len(listcheckin2) > 0:
        print("on entamme la boucle pour les checkin")
        confeature=0
        confeature2=-1
        dateact=datetime.datetime.strptime(listcheckin2[0][1], '%Y-%m-%d %H:%M:%S')
        #--print(dateact)
        notactive=0
        index2 = 1
        #objprecedent= listcheck[0]  #On initialise l'objet précédent en tant que premier enregistrement de la liste de checkin/checkout, car il n'y a pas d'objet précédent pour le moment
        #featureprecedent=listcheckin2[0][3]
        obj = Calcul(index2)
        objprecedent= obj
        while confeature < len(listfeature):  #Tant que countfeature n'est pas égal à la longueur de listfeature, c'est que les enregistrements avec une ou plusieurs feature de listfeature n'ont pas été récupérées
            wantedfeature=listfeature[confeature][1]  #L'idée va être de parcourir la listcheck à la recherche des enregistrement qui possède une feature en particulier (qui change à chaque tour de boucle)
            for q in listfeatureCI:
                if q[1]==wantedfeature:
                    confeature2+=1
            #--print("La feature recherchée est maintenant: "+wantedfeature)
            featurecomplete=0
            l=0
            while l < len(listcheckin2):   #On va parcourir la listcheck dans son entièreté mais avec un while
                date2 = listcheckin2[l][1]
                id2 = listcheckin2[l][2]        #On initialise les variables qu'on voudra afficher plus tard. 
                feature2 = listcheckin2[l][3]   #Les champs importants correspondent aux indices 0,1,2,3,4 de chaque enregistrement (c'est l'ordre qui a été determiné dans la requête SQL)
                nb_token2 = listcheckin2[l][4]
                #print("ID: "+str(obj.id)    +obj.feature+"   nb_token: "+str(obj.tokens)) 
                #print("groupe date "+str(obj.groupedate) + "   groupe id "+str(obj.groupeid))
                #--print(feature2)
                #--print(id2)
                if feature2 == wantedfeature: #Si la feature est bien celle souhaitée
                    if str(datetime.datetime.strptime(date2, '%Y-%m-%d %H:%M:%S') - dateact) in delay : #Si le délai est inférieur à 10s (on fait la soustraction de la date actuelle et de la date de l'enregistrement)
                        if date2 not in obj.groupedate:
                            obj.add_to_groupdate(date2)  #On ajoute la date à la liste de date de l'objet actuel si elle n'y est pas déjà
                        obj.add_to_groupid(id2)  #Dans tous les cas, on ajoute l'id à la liste d'id de l'objet actuel (car il ne peut pas déjà y être)
                        #--print(obj.groupeid)
                        obj.tokens += nb_token2  #On ajoute le nombre de token de l'enregistrement à ceux de l'objet
                        obj.feature = feature2   #Pour le premier tour de boucle qui arrive jusqu'ici, on indique que la feature de l'objet est celle de l'enregistrement
                        featurecomplete+=1
                        #print("featurecomplete: "+ str(featurecomplete))
                        #print("l'élément confeature de listfeature "+str(listfeatureCI[confeature2]))
                        #print("ce qui est attendu à la fin: "+str(listfeatureCI[confeature2][2]))
                        if str(featurecomplete)==str(listfeatureCI[confeature2][2]-1):
                            #--print("featurecomplete est complete !")
                            listobject2.append(objprecedent)
                            #--print("objet ajouté à la liste des objets...")
                            #indexid+=1
                            #obj = Calcul(indexid)
                            #dateact = startdate
                    else:
                        #--print("Le délai de 10s est dépassé")
                        if confeature!=0 or notactive!=0:
                            listobject2.append(objprecedent) #Si le délai de 10s est dépassé on ajoute l'objet précédant à la liste d'objet 
                            #--print("objet ajouté à la liste des objets...")
                            index2+=1
                        obj = Calcul(index2)   #Et on passe à un nouvel objet
                        dateact = datetime.datetime.strptime(date2, '%Y-%m-%d %H:%M:%S') #Il faut donc indiquer que la nouvelle date à comparer est celle de ce nouvel objet
                        if date2 not in obj.groupedate:
                            obj.add_to_groupdate(date2)
                        obj.add_to_groupid(id2)
                        #--print(obj.groupeid)
                        obj.tokens += nb_token2  #Puisque c'est la première instance d'un nouvel objet, on ajoute directement les champs date, id, nombre de token, et feature à ce nouvel objet
                        obj.feature = feature2   #On en aura besoin pour faire la comparaison avec les enregistrements suivants
                        if confeature==0 and notactive==0:
                            objprecedent=obj  
                            notactive=1
                else:
                    #--print("La feature n'est pas égale à celle recherchée")
                    l+=1
                #-- print("---------------------------------------------------------------------------------")
                    continue    #On passe au tour de boucle suivant directement
                l+=1    
                #print("ID: "+str(obj.id)    +obj.feature+"   nb_token: "+str(obj.tokens)) 
                #print("groupe date "+str(obj.groupedate) + "   groupe id "+str(obj.groupeid))
                #--print("-----------------------------------------------------------------------------------------------------")
                objprecedent=obj
                #featureprecedent= feature 
            #print("listobject "+str(listobject))
            #print("listcheckin "+str(listcheckin))
            #print(countcheckin)
            #print(countcheckout)
            listobject2.append(objprecedent)
            #--print("objet ajouté à la liste des objets...")
            #dateact=datetime.datetime.strptime(listcheckin2[0][1], '%Y-%m-%d %H:%M:%S')
            dateact=date_demarrage
            confeature+=1
            #--print("countfeature est maintenant: "+str(countfeature))
        listobject2.append(objprecedent)
        #--print("objet ajouté à la liste des objets...")
        #print(listcheckin2)
        #print(len(listcheckin2))

        """---------CSV 2--------"""

        with open('usage_tri_checkin.csv', 'a', newline='') as csv_tri_checkin:
            csvwriter = csv.writer(csv_tri_checkin, delimiter=';',
                                    quotechar=';', quoting=csv.QUOTE_MINIMAL)
            objectbefore2=Calcul(0)
            for object2 in listobject2:
                if object2.id == objectbefore2.id and object2.feature == objectbefore2.feature and object2.tokens == objectbefore2.tokens and object2.groupeid == objectbefore2.groupeid and object2.groupedate == objectbefore2.groupedate :
                    continue
                else:
                    csvwriter.writerow([object2.id, object2.feature, object2.tokens, object2.groupeid, object2.groupedate])
                    objectbefore2 = object2

    """-------------------------------------------Boucle de rassemblement-------------------------------------------"""
    if len(listobject) > 0 or len(listobject2) > 0:
        print("on tente le rassemblement")
        for checkin in listobject2: #On parcourt la liste d'objets qui ont pour action checkin
            #--print("nouveau checkin !")
            added=0
            id3 = checkin.id
            feature3 = checkin.feature
            count_token = checkin.tokens    #Pour faire les comparaisons, seul l'id, la feature et les tokens sont necessaires (et encore pour les tokens je suis pas tout à fait sûr)
            for checkout in listobject:    #On parcourt la listye d'objets qui ont pour action checkout, pour pouvoir faire des comparaisons
                #--print("prochain checkout !")
                #--print("ID du checkin: "+ str(checkin.groupeid[0]))
                #--print("feature3: "+ feature3)
                #--print("feature du checkout: "+ checkout.feature)
                #--print("count_token: "+ str(count_token))
                #--print("nb de tokens du checkout: "+ str(checkout.tokens))
                #--print(nbdate)
                #--delta="DELTA_DEFORMATION"
                #--if delta in checkin.feature:
                if feature3 == checkout.feature:     #La feature doit être la même
                    if count_token == checkout.tokens:   #Le nombre de tokens aussi
                        if added==0:
                            if checkout.alradded == 0:
                                for date in checkin.groupedate: #On parcourt la liste de date de l'objet checkin
                                    timedifference = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')-datetime.datetime.strptime(checkout.groupedate[0], '%Y-%m-%d %H:%M:%S')
                                    #--print("-----------------------------------------------------")
                                    #--print("feature3: "+ feature3)
                                    #--print("id de l'enr. du checkin: "+ str(checkin.groupeid[0]))
                                    #--print(date)
                                    #--print(checkout.groupedate[0])
                                    #--print(timedifference.days)
                                    if timedifference.total_seconds() >= 0:
                                        if date not in checkout.groupedate:
                                            checkout.add_to_groupdate(date)  #On l'ajoute
                                        checkout.alradded=1
                                        if len(checkout.groupeid)<=count_token:
                                            #--print("Liste des id "+str(checkout.groupeid))
                                            for identifiant in checkin.groupeid:
                                                #--print("id du checkin: "+str(identifiant))
                                                if identifiant not in checkout.groupeid:
                                                    checkout.add_to_groupid(identifiant) #On ajoute aussi l'ID
                                                    #--print("Liste des id update: "+str(checkout.groupeid))
                                                    added=1
                                if len(checkout.groupedate) > (checkout.nbdate)*2:
                                    #--print(checkout.groupedate)
                                    if len(checkout.groupedate) > 0 and len(checkout.groupeid) > 0:
                                        #--print(len(checkout.groupedate))
                                            #--for s in range(len(checkout.groupeid),len(checkout.groupedate)-1):
                                        s=0
                                        while s<len(checkout.groupedate)-(len(checkout.groupeid)):
                                            #--print(s)
                                            del checkout.groupedate[len(checkout.groupeid)]
                                            s+=1
                                        #--print(checkout.groupedate)
                                        #--print("...")
                                        #--print("Liste des dates update: "+str(checkout.groupedate))
                                #--print("longueur de la liste des id: "+str(len(checkout.groupeid)))
                                #--print("nombre de tokens: "+str(count_token))
                            checkoutprec=checkout
                            #print("ID: "+str(obj.id)+"   action: "+action+"   "+obj.feature+"   nb_token: "+str(obj.tokens)) 
                            #print("groupe date "+str(obj.groupedate) + "   groupe id "+str(obj.groupeid))
                            #print("-----------------------------------------------------------------------------------------------------")

        """---------CSV 3--------"""

        with open('usage_tri_checkall.csv', 'a', newline='') as csv_tri_checkall:
            csvwriter = csv.writer(csv_tri_checkall, delimiter=';',
                                    quotechar=';', quoting=csv.QUOTE_MINIMAL)
            objectbefore3=Calcul(0)
            for object3 in listobject:
                if object3.id == objectbefore3.id and object3.feature == objectbefore3.feature and object3.tokens == objectbefore3.tokens and object3.groupeid == objectbefore3.groupeid and object3.groupedate == objectbefore3.groupedate :
                    continue
                elif len(object3.groupedate) <= 0:
                    continue 
                else:
                    date_debut= object3.groupedate[0]
                    date_fin= object3.groupedate[-1]
                    date_diff= datetime.datetime.strptime(date_fin, '%Y-%m-%d %H:%M:%S')-datetime.datetime.strptime(date_debut, '%Y-%m-%d %H:%M:%S')
                    csvwriter.writerow([object3.id, object3.feature, object3.tokens, object3.groupeid, object3.groupedate, date_debut, date_fin, date_diff])
                    objectbefore3 = object3
#else:
    #print("Au moins une des dates que vous avez saisi ne figure pas dans la base de donnée.")
    #print("Merci de bien vouloir réessayer en saisissant deux dates présentes dans la base de donnée.")



def assemblage():

    """-------------------------------------------------------------------------------Connexion à la BDD------------------------------------------------------------------------------------------"""

    try:
        database= "usage.db"
        conn = sqlite3.connect(database)
        cur = conn.cursor()
        print(database + " est correctement connectée à SQLite")
        liststartshut=[]
        liststartup=[]
        listshutdown=[]


        """-------------------------------------------------------------------------------REQUETES------------------------------------------------------------------------------------------------"""
        
        
        startshutquery = f"""select action, datetime(time, 'unixepoch', 'localtime') as date_depart from usage where action = 'STARTUP' or action='SHUTDOWN'"""
        #print(startshutquery)
        cur.execute(startshutquery)
        res1 = cur.fetchall()
        for i in res1:
            liststartshut.append(i)
        startupquery = f"""select datetime(time, 'unixepoch', 'localtime') as date_depart from usage where action = 'STARTUP'"""
        #print(startupquery)
        cur.execute(startupquery)
        res2 = cur.fetchall()
        for i in res2:
            liststartup.append(i)
        shutdownquery = f"""select datetime(time, 'unixepoch', 'localtime') as date_fin from usage where action = 'SHUTDOWN'"""
        #print(shutdownquery)
        cur.execute(shutdownquery)
        res3 = cur.fetchall()
        for i in res3:
            listshutdown.append(i)
    
    except sqlite3.Error as error:
        print("Erreur lors de la connexion à SQLite", error)

    file = 'usage_tri_checkout.csv'
    if(os.path.exists(file) and os.path.isfile(file)):
        os.remove(file)

    file2 = 'usage_tri_checkin.csv'
    if(os.path.exists(file2) and os.path.isfile(file2)):
        os.remove(file2)

    file3 = 'usage_tri_checkall.csv'
    if(os.path.exists(file3) and os.path.isfile(file3)):
        os.remove(file3)

    col1="id_calcul"
    col2="feature"
    col3="nb_token"
    col4="groupe_id"
    col5="groupe_date"

    with open('usage_tri_checkout.csv', 'w', newline='') as csv_tri_checkout:
        csvwriter = csv.writer(csv_tri_checkout, delimiter=';',
        quotechar=';', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow([col1,col2,col3,col4,col5])

    with open('usage_tri_checkin.csv', 'w', newline='') as csv_tri_checkin:
                csvwriter = csv.writer(csv_tri_checkin, delimiter=';',
                quotechar=';', quoting=csv.QUOTE_MINIMAL)
                csvwriter.writerow([col1,col2,col3,col4,col5])

    col1="id_calcul"
    col2="feature"
    col3="nb_token"
    col4="groupe_id"
    col5="groupe_date"
    col6="debut_calcul"
    col7="fin_calcul"
    col8="date_diff"

    with open('usage_tri_checkall.csv', 'a', newline='') as csv_tri_checkall:
        csvwriter = csv.writer(csv_tri_checkall, delimiter=';',
        quotechar=';', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow([col1,col2,col3,col4,col5,col6,col7,col8])


    indexid = index(0)
    print(type(indexid.indexid))
    print("Lancement de la fonction d'assemblage !")
    for i in range(len(listshutdown)):
        date_de_demarrage= str(liststartup[i])[2:21] #On sélectionne uniquement la partie de l'enregistrement qui correspond à la date et on la convertie en string
        date_de_larret= str(listshutdown[i])[2:21]
        indexid.indexid+=1 #l'indexid est incrémenté à chaque passage de boucle
        agregat_checkout(date_de_demarrage,date_de_larret,indexid)
        print("Les données ont été ajoutées à leur csv respectifs.")
        print("Les objets checkout ont été ajoutés au fichier usage_tri_checkout.csv")
        print("Les objets checkin ont été ajoutés au fichier usage_tri_checkin.csv")
        print("Les objets checkout groupés avec les objets checkin ont été ajoutés au fichier usage_tri_checkall.csv")

if __name__ == "__main__":
    if analysis == "token" or analysis == "token usage":
        usage_evolution_licence()
    elif analysis == "uptime" or analysis == "server uptime":
        usage_temps_activite()
    elif analysis == "aggregate" or analysis == "aggregate action":
        assemblage()