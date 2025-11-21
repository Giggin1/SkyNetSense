
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from db import connessione
from functools import wraps

# Crea l'app Flask e usa la cartella FrontEnd come static folder (path inline)
app = Flask(
    __name__,
    static_folder="../FrontEnd",
    static_url_path=""
)

@app.route("/", methods=["GET"])
def home():
    # Restituisce il file index.html dalla cartella FrontEnd
    return app.send_static_file("index.html")


@app.route("/registrazione")
def view_registrazione():
    # Cerca il file nella cartella static (FrontEnd)
    return app.send_static_file("registrazione.html")


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

    sql_stazioni = """
        SELECT
            cf_utente,
            nome_stazione,
            paese,
            regione,
            citta,
            provincia,
            cap,
            ultimo_dato_inviato
        FROM Stazioni
        ORDER BY regione, citta, nome_stazione
    """

    cur_st.execute(sql_stazioni)

    stazioni = []

    # scorro tutte le stazioni
    for (
        cf_utente,
        nome_stazione,
        paese,
        regione,
        citta,
        provincia,
        cap,
        ultimo_dato_inviato
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
            "dati": dati
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



# Avvia il server Flask se eseguiamo direttamente questo file
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

