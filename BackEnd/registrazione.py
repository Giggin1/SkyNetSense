from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Blueprint
from db import connessione
from functools import wraps
from decoratori import login_required

registrazione_bp = Blueprint('registrazione', __name__)

@registrazione_bp.route("/api/public/register", methods=["POST"])
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
