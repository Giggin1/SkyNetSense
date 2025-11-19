import os
from flask import Flask, request, jsonify
from db import connessione

# Cartella FrontEnd (relativa alla posizione di questo file)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "FrontEnd")

# Crea l'app Flask e usa la cartella FrontEnd come static folder
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

@app.route("/", methods=["GET"])
def home():
    # Restituisce il file index.html dalla cartella FrontEnd
    return app.send_static_file("index.html")

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
            WHERE cf_utente = ?
              AND nome_stazione = ?
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
                WHERE d.cf_utente = ?
                  AND d.nome_stazione = ?
                  AND d.timestamp_lettura = ?
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



# Avvia il server Flask se eseguiamo direttamente questo file
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

