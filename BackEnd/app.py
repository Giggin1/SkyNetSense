from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from db import connessione
from functools import wraps
import time

# Crea l'app Flask e usa la cartella FrontEnd come static folder (path inline)
app = Flask(
    __name__,
    static_folder="../FrontEnd",
    static_url_path=""
)

app.secret_key = "DATECIIL30ELODE"

# --- Configurazione anti-bruteforce lato backend ---
# quante volte si può sbagliare di fila prima del blocco
MAX_ATTEMPTS = 5

# durata del blocco in secondi (per ora sono 10 secondi)
LOCK_SECONDS = 20

# Dizionario in memoria:
# chiave = "ip:email"
# valore = {"fails": numero_tentativi, "lock_until": timestamp_unix}
login_attempts = {}


def get_client_ip():
    """
    Ritorna l'IP del client.
    In futuro, se metterai un proxy (Nginx, ecc.), useremo X-Forwarded-For.
    """
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        # può contenere più IP separati da virgola, prendiamo il primo
        return forwarded_for.split(",")[0].strip()

    return request.remote_addr or "unknown"


# Decoratore per proteggere le rotte che richiedono login autenticato 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Non autenticato"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route("/", methods=["GET"])
def home():
    # Restituisce il file index.html dalla cartella FrontEnd
    return app.send_static_file("HTML/index.html")


@app.route("/registrazione")
def view_registrazione():
    # Cerca il file nella cartella static (FrontEnd)
    return app.send_static_file("HTML/registrazione.html")


@app.route("/login")
def view_login():
    # Cerca il file nella cartella static (FrontEnd)
    return app.send_static_file("HTML/login.html")


@app.route("/stazioni")
def view_stazioni():
    # Restituisce il file Stazioni.html dalla cartella FrontEnd
    return app.send_static_file("HTML/stazioni.html")







#Api per ottenere il file json delle stazioni relative all'utente loggato
@app.route("/api/auth/my-stations", methods=["GET"])
@login_required
def my_stations():
    cf_utente = session.get("user_cf")

    conn = connessione()
    if conn is None:
        return jsonify({"error": "Errore di connessione al database"}), 500

    cur = conn.cursor()
    try:
        sql = """
            SELECT
                cf_utente,
                nome_stazione,
                data_installazione,
                ultimo_dato_inviato,
                paese,
                regione,
                citta,
                provincia,
                latitudine.
                longitudine,
                cap
            FROM Stazioni
            WHERE cf_utente = %s
            ORDER BY nome_stazione
        """
        cur.execute(sql, (cf_utente,))
        stazioni = []
        for (
            cf,
            nome_stazione,
            data_installazione,
            ultimo_dato_inviato,
            paese,
            regione,
            citta,
            provincia,
            latiudine,
            longitudine,
            cap
        ) in cur:

            stazioni.append({
                "cf_utente": cf,
                "nome_stazione": nome_stazione,
                "data_installazione": (
                    data_installazione.strftime("%Y-%m-%d")
                    if data_installazione else None
                ),
                "ultimo_dato_inviato": (
                    ultimo_dato_inviato.strftime("%Y-%m-%d %H:%M:%S")
                    if ultimo_dato_inviato else None
                ),
                "paese": paese,
                "regione": regione,
                "citta": citta,
                "provincia": provincia,
                "cap": cap,
                "latiudine": latiudine,
                "longitudine": longitudine
            })

        return jsonify(stazioni), 200

    except Exception as e:
        print("Errore my_stations:", e)
        return jsonify({"error": "Errore interno del server"}), 500
    finally:
        cur.close()
        conn.close()





# Definiamo un endpoint GET /api/public/stazioni
@app.route("/api/public/stazioni", methods=["GET"])
def get_stazioni():
    """
    Ora questa funzione legge:
    - tutte le stazioni dalla tabella Stazioni
    - per ogni stazione, l'ULTIMO set di dati dalla tabella Dati (+ Sensori)
    """
    conn = connessione()
    if conn is None:
        return jsonify({"error": "Errore di connessione al database"}), 500

    cur_st = conn.cursor()

    # Query per prendere tutte le stazioni
    sql_stazioni = """
        SELECT
            cf_utente,
            nome_stazione,
            ultimo_dato_inviato,
            paese,
            regione,
            citta,
            provincia,
            cap,
            latitudine,
            longitudine
        FROM Stazioni
        ORDER BY regione, citta, nome_stazione
    """
    # Eseguo la query
    cur_st.execute(sql_stazioni)

    stazioni = []

    # scorro tutte le stazioni
    for (
            cf_utente,
            nome_stazione,
            ultimo_dato_inviato,
            paese,
            regione,
            citta,
            provincia,
            cap,
            latitudine,
            longitudine
    ) in cur_st:

        # ==============================
        # 1) Trovo l'ULTIMO timestamp_lettura per questa stazione
        # ==============================
        cur_ts = conn.cursor()
        sql_ultimo_ts = """
            SELECT MAX(timestamp_lettura)
            FROM Dati
            WHERE cf_utente = %s
              AND nome_stazione = %s
        """
        cur_ts.execute(sql_ultimo_ts, (cf_utente, nome_stazione))
        row_ts = cur_ts.fetchone()
        cur_ts.close()

        ultimo_ts = row_ts[0] if row_ts is not None else None

        dati = {}
        ultimo_dato_str = None

        # ==============================
        # 2) Se esiste almeno una misura, prendo TUTTI i dati di quel timestamp
        # ==============================
        if ultimo_ts is not None:
            cur_dati = conn.cursor()
            sql_dati = """
                SELECT
                    d.nome_sensore,
                    d.valore,
                    s.unita
                FROM Dati d
                JOIN Sensori s
                  ON s.modello = d.modello
                 AND s.nome    = d.nome_sensore
                WHERE d.cf_utente = %s
                  AND d.nome_stazione = %s
                  AND d.timestamp_lettura = %s
                ORDER BY d.nome_sensore
            """
            cur_dati.execute(sql_dati, (cf_utente, nome_stazione, ultimo_ts))

            for nome_sensore, valore, unita in cur_dati:
                if unita is None:
                    unita = ""
                testo_valore = f"{valore} {unita}".strip()
                dati[nome_sensore] = testo_valore

            cur_dati.close()

            # formatto il timestamp come stringa
            ultimo_dato_str = ultimo_ts.strftime("%Y-%m-%d %H:%M:%S")

        # ==============================
        # 3) Se NON ho trovato dati in Dati, uso eventualmente ultimo_dato_inviato
        # ==============================
        if ultimo_dato_str is None and ultimo_dato_inviato is not None:
            ultimo_dato_str = ultimo_dato_inviato.strftime("%Y-%m-%d %H:%M:%S")

        # ==============================
        # 4) Costruisco l'oggetto stazione per il JSON
        # ==============================
        stazioni.append({
            "cf_utente": cf_utente,
            "nome_stazione": nome_stazione,
            "paese": paese,
            "regione": regione,
            "citta": citta,
            "provincia": provincia,
            "cap": cap,
            "ultimo_dato": ultimo_dato_str,
            "dati": dati,
            "latitudine": latitudine,
            "longitudine": longitudine
        })

    cur_st.close()
    conn.close()

    return jsonify(stazioni)


# Endpoint per la registrazione pubblica
@app.route("/api/public/register", methods=["POST"])
def register_user():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Payload non valido"}), 400

    nickname = (data.get("nickname") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not nickname or not email or not password:
        return jsonify({"error": "Inserisci nickname, email e password"}), 400

    conn = connessione()
    if conn is None:
        return jsonify({"error": "Errore di connessione al database"}), 500

    cur = conn.cursor()
    try:
        # Verifica email già presente
        cur.execute("SELECT CF FROM utenti WHERE email = %s", (email,))
        row = cur.fetchone()
        if row is not None:
            return jsonify({"error": "Email già registrata"}), 409

        # Inserisci nuovo utente
        cur.execute(
            "INSERT INTO utenti (CF, nickname, email, password, nome, cognome) VALUES (%s, %s, %s, %s, %s, %s)",
            (data.get("codice_fiscale"), nickname, email, password , data.get("nome"), data.get("cognome")),
        )
        conn.commit()
        return jsonify({"message": "Registrazione completata"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Errore server: {e}"}), 500
    finally:
        try:
            cur.close()
        except:
            pass
        conn.close()

# Endpoint per il login
# Sostituisci la tua funzione login_user attuale con questa completa

# Endpoint per il login
@app.route("/api/public/login", methods=["POST"])
def login_user():
    # Timestamp attuale per la gestione del blocco
    now = time.time()

    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Payload non valido"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Inserisci email e password"}), 400

    # ------------------------------
    # 1) Controllo blocco per IP + email
    # ------------------------------
    ip = get_client_ip()
    key = f"{ip}:{email}"

    # Recupera (se esiste) il record per questa coppia IP+email
    record = login_attempts.get(key, {"fails": 0, "lock_until": 0})

    # Se l'utente è ancora bloccato, non facciamo nemmeno la query al DB
    if record["lock_until"] > now:
        remaining = int(record["lock_until"] - now)
        return (
            jsonify(
                {"error": f"Troppi tentativi falliti. Riprova tra {remaining} secondi."}
            ),
            429,  # Too Many Requests
        )

    # ------------------------------
    # 2) Verifica credenziali su DB
    # ------------------------------
    conn = connessione()
    if conn is None:
        return jsonify({"error": "Errore di connessione al database"}), 500

    cur = conn.cursor()
    try:
        # Verifica credenziali
        cur.execute(
            "SELECT CF, nickname FROM utenti WHERE email = %s AND password = %s",
            (email, password),
        )

        account = cur.fetchone()  # Recupera la riga trovata (se esiste)

        if account:
           

            # account[0] = CF, account[1] = nickname
            # ---> SALVIAMO I DATI IN SESSIONE <---
            session.permanent = True
            session["user_cf"] = account[0]
            session["nickname"] = account[1]
            session["logged_in"] = True

            return (
                jsonify(
                    {
                        "message": "Login effettuato con successo",
                        "nickname": account[1],
                        "redirect": "/",  # Diciamo al frontend dove andare
                    }
                ),
                200,
            )

    except Exception as e:
        # In caso di errore SQL
        print(f"Errore SQL: {e}")  # Utile per il debug nella console
        conn.rollback()
        return jsonify({"error": "Errore interno del server"}), 500
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()



@app.route("/api/auth/logout")
def logout():
    session.clear() # Rimuove tutti i dati dalla sessione
    return redirect(url_for('home')) # O restituisci un JSON se preferisci gestirlo via JS

@app.route("/api/auth/status")
def session_status():
    if session.get("logged_in"):
        return jsonify({
            "logged_in": True, 
            "nickname": session["nickname"],
            "cf": session["user_cf"]
        })
    else:
        return jsonify({"logged_in": False})


@app.route("/api/station/data", methods=["POST"])
def ricevi_dati_stazione():
    data = request.get_json(force=True)

    cf_utente = data.get("cf_utente")
    nome_stazione = data.get("nome_stazione")
    dati = data.get("dati", [])  # lista di misure

    # Controllo che il JSON abbia le info minime
    if not cf_utente or not nome_stazione or not dati:
        return jsonify({"error": "Payload incompleto"}), 400

    conn = connessione()
    if conn is None:
        return jsonify({"error": "Errore di connessione al database"}), 500

    cur = conn.cursor()
    try:
        # 1) Controllo che la stazione esista
        cur.execute(
            "SELECT 1 FROM Stazioni WHERE cf_utente = %s AND nome_stazione = %s",
            (cf_utente, nome_stazione)
        )
        row = cur.fetchone()
        if row is None:
            return jsonify({"error": "Stazione non trovata"}), 404

        # 2) Per ogni misura ricevuta
        for misura in dati:
            modello = misura.get("modello")            # es: 'MQ-135'
            nome_sensore = misura.get("nome_sensore")  # es: 'MQ135_raw'
            valore = misura.get("valore")

            # salto le misure incomplete
            if modello is None or nome_sensore is None or valore is None:
                continue

            # 2a) Verifico / creo il sensore in Sensori
            cur.execute(
                "SELECT 1 FROM Sensori WHERE modello = %s AND nome = %s",
                (modello, nome_sensore)
            )
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO Sensori (modello, nome, unita) VALUES (%s, %s, %s)",
                    (modello, nome_sensore, None)
                )

            # 2b) Verifico / creo l'associazione in Stazioni_Sensori
            cur.execute(
                """
                SELECT 1 FROM Stazioni_Sensori
                WHERE cf_utente = %s AND nome_stazione = %s
                      AND modello = %s AND nome_sensore = %s
                """,
                (cf_utente, nome_stazione, modello, nome_sensore)
            )
            if cur.fetchone() is None:
                cur.execute(
                    """
                    INSERT INTO Stazioni_Sensori
                    (cf_utente, nome_stazione, modello, nome_sensore)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (cf_utente, nome_stazione, modello, nome_sensore)
                )

            # 2c) Inserisco il dato in Dati
            cur.execute(
                """
                INSERT INTO Dati
                (timestamp_lettura, cf_utente, nome_stazione, modello, nome_sensore, valore)
                VALUES (NOW(), %s, %s, %s, %s, %s)
                """,
                (cf_utente, nome_stazione, modello, nome_sensore, valore)
            )

        # 3) Aggiorno ultimo_dato_inviato nella tabella Stazioni
        cur.execute(
            """
            UPDATE Stazioni
            SET ultimo_dato_inviato = NOW()
            WHERE cf_utente = %s AND nome_stazione = %s
            """,
            (cf_utente, nome_stazione)
        )

        conn.commit()
        return jsonify({"message": "Dati salvati correttamente"}), 201

    except Exception as e:
        print("Errore inserimento dati stazione:", e)
        conn.rollback()
        return jsonify({"error": "Errore interno del server"}), 500

    finally:
        cur.close()
        conn.close()


# Avvia il server Flask se eseguiamo direttamente questo file
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

