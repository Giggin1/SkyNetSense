from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Blueprint
from db import connessione
from decoratori import login_required
import time


# --- Configurazione anti-bruteforce lato backend ---
# quante volte si può sbagliare di fila prima del blocco
MAX_ATTEMPTS = 5

# durata del blocco in secondi (per ora sono 10 secondi)
LOCK_SECONDS = 20

login_attempts = {}

login_bp = Blueprint('login', __name__)
@login_bp.route("/api/public/login", methods=["POST"])
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
            429, 
        )
    
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