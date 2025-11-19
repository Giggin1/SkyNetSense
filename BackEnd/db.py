#File per la connessione al database
import mariadb

def connessione() :
    try :
        conn = mariadb.connect(
            host = "127.0.0.1",
            user = "root",
            password = "",
            port = 3306,
            database = "SkyNetSense"
        )
        return conn
    except mariadb.Error as e : 
        print(f"Errore connessione DB : {e}")
        return None