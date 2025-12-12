from flask import Flask, jsonify, session, Blueprint
from functools import wraps

decoratori_bp = Blueprint('decoratori', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "Non autenticato"}), 401
        return f(*args, **kwargs)
    return decorated_function