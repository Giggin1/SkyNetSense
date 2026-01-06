from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Blueprint
from db import connessione
from functools import wraps



main_bp = Blueprint('main', __name__)

@main_bp.route("/api/public/stazioni", methods=["GET"])
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

    #Query per prendere tutte le stazioni
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
    #Eseguo la query
    cur_st.execute(sql_stazioni)

    stazioni = []

    #scorro tutte le stazioni
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

       
        #Trovo l'ULTIMO timestamp_lettura per questa stazione
        
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

       
        #Se esiste almeno una misura, prendo TUTTI i dati di quel timestamp
       
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

        
        #Se NON ho trovato dati in Dati, uso eventualmente ultimo_dato_inviato
        if ultimo_dato_str is None and ultimo_dato_inviato is not None:
            ultimo_dato_str = ultimo_dato_inviato.strftime("%Y-%m-%d %H:%M:%S")

      #costruisco il json
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





@main_bp.route("/api/auth/status")
def session_status():
    if session.get("logged_in"):
        return jsonify({
            "logged_in": True, 
            "nickname": session["nickname"],
            "cf": session["user_cf"]
        })
    else:
        return jsonify({"logged_in": False})
    






@main_bp.route("/api/auth/logout")
def logout():
    session.clear() # Rimuove tutti i dati dalla sessione
    return redirect(url_for('home')) # O restituisci un JSON se preferisci gestirlo via JS



# Endpoint per ottenere i sensori di una stazione specifica 

@main_bp.route("/api/public/sensors", methods=["GET"])
def public_sensors():
    cf_utente = request.args.get("cf_utente") or request.args.get("cf")
    nome_stazione = request.args.get("nome_stazione") or request.args.get("stazione")

    if not cf_utente or not nome_stazione:
        return jsonify({"error": "Parametri mancanti: cf_utente, nome_stazione"}), 400

    conn = connessione()
    if conn is None:
        return jsonify({"error": "Errore connessione DB"}), 500

    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT d.modello, d.nome_sensore, COALESCE(s.unita,'')
            FROM Dati d
            LEFT JOIN Sensori s
              ON s.modello = d.modello
             AND s.nome    = d.nome_sensore
            WHERE d.cf_utente = %s
              AND d.nome_stazione = %s
            ORDER BY d.modello, d.nome_sensore
        """, (cf_utente, nome_stazione))

        sensors = [
            {"modello": m, "nome_sensore": n, "unita": u}
            for (m, n, u) in cur.fetchall()
        ]
        return jsonify({"sensors": sensors}), 200
    finally:
        cur.close()
        conn.close()

# Endpoint per ottenere lo storico dei dati di un sensore specifico

@main_bp.route("/api/public/history", methods=["GET"])
def public_history():
    cf_utente = request.args.get("cf_utente") or request.args.get("cf")
    nome_stazione = request.args.get("nome_stazione") or request.args.get("stazione")
    modello = request.args.get("modello")
    nome_sensore = request.args.get("nome_sensore")
    limit = request.args.get("limit", "200")

    if not all([cf_utente, nome_stazione, modello, nome_sensore]):
        return jsonify({"error": "Parametri mancanti: cf_utente, nome_stazione, modello, nome_sensore"}), 400

    try:
        limit = int(limit)
    except:
        limit = 200
    limit = max(1, min(limit, 2000))

    conn = connessione()
    if conn is None:
        return jsonify({"error": "Errore connessione DB"}), 500

    cur = conn.cursor()
    try:
        cur.execute(f"""
            SELECT d.timestamp_lettura, d.valore, COALESCE(s.unita,'')
            FROM Dati d
            LEFT JOIN Sensori s
              ON s.modello = d.modello
             AND s.nome    = d.nome_sensore
            WHERE d.cf_utente = %s
              AND d.nome_stazione = %s
              AND d.modello = %s
              AND d.nome_sensore = %s
            ORDER BY d.timestamp_lettura DESC
            LIMIT {limit}
        """, (cf_utente, nome_stazione, modello, nome_sensore))

        rows = cur.fetchall()

        points = []
        for ts, val, unita in reversed(rows):
            points.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "value": float(val)
            })

        return jsonify({
            "modello": modello,
            "nome_sensore": nome_sensore,
            "unita": (rows[0][2] if rows else ""),
            "points": points
        }), 200
    finally:
        cur.close()
        conn.close()
