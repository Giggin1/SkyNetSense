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
def get_stazioni_fake():
    """
    Questa funzione viene eseguita quando il browser chiama:
    GET http://127.0.0.1:5000/api/public/stazioni
    """
    # Dati FINTI: stessa struttura che useremo poi con il DB
    stazioni = [
        {
            "cf_utente": "RSSMRA99A01H501X",
            "nome_stazione": "Skynetsense_Casa",
            "paese": "Italia",
            "regione": "Lombardia",
            "citta": "Milano",
            "provincia": "MI",
            "cap": "20100",
            "ultimo_dato": "2025-11-18 10:15:00",
            "dati": {
                "Temperatura": "22.0 °C",
                "Umidità": "44 %",
                "PM2.5": "8.4 µg/m³"
            }
        },
        {
            "cf_utente": "BNCLNZ01B45F205Y",
            "nome_stazione": "Skynetsense_Campagna",
            "paese": "Italia",
            "regione": "Lazio",
            "citta": "Viterbo",
            "provincia": "VT",
            "cap": "01100",
            "ultimo_dato": "2025-11-18 09:50:00",
            "dati": {
                "Temperatura": "16.8 °C",
                "Umidità": "61.5 %",
                "PM10": "12.1 µg/m³"
            }
        }
    ]

    # jsonify converte la lista Python in JSON per il browser
    return jsonify(stazioni)


# Avvia il server Flask se eseguiamo direttamente questo file
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

