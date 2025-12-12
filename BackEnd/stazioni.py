from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Blueprint
from db import connessione
from functools import wraps
from decoratori import login_required

stazioni_bp = Blueprint('stazioni', __name__)


@stazioni_bp.route("/api/auth/my-stations", methods=["GET"])
@login_required
def my_stations():
    cf_utente = session.get("user_cf")
    print("CF utente sessione:", cf_utente)
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
                latitudine,
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
            latitudine,
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
                "latitudine": latitudine,
                "longitudine": longitudine
            })

        return jsonify(stazioni), 200

    except Exception as e:
        print("Errore my_stations:", e)
        return jsonify({"error": "Errore interno del server"}), 500
    finally:
        cur.close()
        conn.close()
