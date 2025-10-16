from flask import Flask, request, jsonify
import pyrebase
import hashlib
import os
from datetime import datetime

app = Flask(__name__)

# Reuse the same Firebase config as main.py
firebaseConfig = {
    "apiKey": "AIzaSyBwSlphAGkdUaNWAFrztz3lcuwnyc6FVVE",
    "authDomain": "bank-management-system-a0944.firebaseapp.com",
    "databaseURL": "https://bank-management-system-a0944-default-rtdb.firebaseio.com/",
    "projectId": "bank-management-system-a0944",
    "storageBucket": "bank-management-system-a0944.appspot.com",
    "messagingSenderId": "306645069933 ",
    "appId": "06645069933:web:767a946990cad6e3da4f64"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

def simple_hash(s):
    return hashlib.sha256(s.encode()).hexdigest()


@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Cloud Bank running"})


@app.route("/balance/<username>")
def balance(username):
    acc = db.child("accounts").child(username).get().val()
    if not acc:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"username": username, "balance": acc.get("balance", 0.0)})


@app.route("/create", methods=["POST"])
def create_account():
    data = request.get_json(force=True)
    required = ["fname", "lname", "user", "password", "phone", "aadhar"]
    if not all(k in data for k in required):
        return jsonify({"error": "missing fields", "required": required}), 400

    username = data["user"].strip()
    user_ref = db.child("accounts").child(username).get()
    if user_ref.val():
        return jsonify({"error": "username exists"}), 409

    payload = {
        "fname": data["fname"],
        "lname": data["lname"],
        "user": username,
        "pass_hash": simple_hash(data["password"]),
        "phone": data["phone"],
        "aadhar": data["aadhar"],
        "balance": 0.0,
        "created_at": datetime.now().isoformat()
    }
    db.child("accounts").child(username).set(payload)
    return jsonify({"ok": True, "user": username}), 201


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
