from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from db import connessione
from functools import wraps
import time
from main import main_bp
from decoratori import login_required
from stazioni import stazioni_bp
from registrazione import registrazione_bp
from login import login_bp

# Crea l'app Flask e usa la cartella FrontEnd come static folder (path inline)
app = Flask(
    __name__,
    static_folder="../FrontEnd",
    static_url_path=""
)

app.register_blueprint(main_bp)
app.register_blueprint(stazioni_bp)
app.register_blueprint(registrazione_bp)
app.register_blueprint(login_bp)



app.secret_key = "DATECIIL30ELODE"


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



#funzione per ricevere i dati dalle stazioni
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

