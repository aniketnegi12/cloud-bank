import os
import hashlib
import random
import time
from datetime import datetime
from flask import Flask, request, jsonify
import pyrebase

# ------------------- CONFIGURE FIREBASE -------------------
firebaseConfig = {
    "apiKey": "AIzaSyBwSlphAGkdUaNWAFrztz3lcuwnyc6FVVE",
    "authDomain": "bank-management-system-a0944.firebaseapp.com",
    "databaseURL": "https://bank-management-system-a0944-default-rtdb.firebaseio.com/",
    "projectId": "bank-management-system-a0944",
    "storageBucket": "bank-management-system-a0944.appspot.com",
    "messagingSenderId": "306645069933",
    "appId": "06645069933:web:767a946990cad6e3da4f64"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

# ------------------- UTILITIES -------------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def simple_hash(s):
    return hashlib.sha256(s.encode()).hexdigest()

def append_txn(username, ttype, amount, other="N/A"):
    txn_id = f"{int(time.time())}{random.randint(1000,9999)}"
    txn = {
        "user": username,
        "type": ttype,
        "amount": amount,
        "other": other,
        "time": now_str(),
        "id": txn_id
    }
    db.child("transactions").push(txn)

# ------------------- FLASK APP -------------------
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "✅ Cloud Bank API is running successfully on Render!"})

# --- Create Account ---
@app.route("/create", methods=["POST"])
def create_account():
    data = request.json
    user = data.get("username")
    password = data.get("password")
    fname = data.get("fname")
    lname = data.get("lname")
    phone = data.get("phone")
    aadhar = data.get("aadhar")

    if not all([user, password, fname, lname, phone, aadhar]):
        return jsonify({"error": "Missing fields"}), 400

    if db.child("accounts").child(user).get().val():
        return jsonify({"error": "Username already exists"}), 400

    acc = {
        "user": user,
        "pass_hash": simple_hash(password),
        "fname": fname,
        "lname": lname,
        "phone": phone,
        "aadhar": aadhar,
        "balance": 0.0
    }
    db.child("accounts").child(user).set(acc)
    return jsonify({"message": f"Account created for {user}"}), 201

# --- Login ---
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = data.get("username")
    password = data.get("password")

    acc = db.child("accounts").child(user).get().val()
    if not acc:
        return jsonify({"error": "No such user"}), 404
    if acc["pass_hash"] != simple_hash(password):
        return jsonify({"error": "Invalid password"}), 403
    return jsonify({"message": "Login successful", "account": acc}), 200

# --- Deposit ---
@app.route("/deposit", methods=["POST"])
def deposit():
    data = request.json
    user = data.get("username")
    amount = float(data.get("amount", 0))

    acc = db.child("accounts").child(user).get().val()
    if not acc:
        return jsonify({"error": "No such user"}), 404

    acc["balance"] += amount
    db.child("accounts").child(user).update({"balance": acc["balance"]})
    append_txn(user, "deposit", amount)
    return jsonify({"message": f"Deposited ₹{amount:.2f}", "balance": acc["balance"]})

# --- Withdraw ---
@app.route("/withdraw", methods=["POST"])
def withdraw():
    data = request.json
    user = data.get("username")
    amount = float(data.get("amount", 0))

    acc = db.child("accounts").child(user).get().val()
    if not acc:
        return jsonify({"error": "No such user"}), 404
    if acc["balance"] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    acc["balance"] -= amount
    db.child("accounts").child(user).update({"balance": acc["balance"]})
    append_txn(user, "withdraw", amount)
    return jsonify({"message": f"Withdrawn ₹{amount:.2f}", "balance": acc["balance"]})

# --- Transfer ---
@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.json
    sender = data.get("sender")
    receiver = data.get("receiver")
    amount = float(data.get("amount", 0))

    s_acc = db.child("accounts").child(sender).get().val()
    r_acc = db.child("accounts").child(receiver).get().val()

    if not s_acc or not r_acc:
        return jsonify({"error": "Invalid sender or receiver"}), 404
    if s_acc["balance"] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    s_acc["balance"] -= amount
    r_acc["balance"] += amount
    db.child("accounts").child(sender).update({"balance": s_acc["balance"]})
    db.child("accounts").child(receiver).update({"balance": r_acc["balance"]})

    append_txn(sender, "transfer_to", amount, receiver)
    append_txn(receiver, "transfer_from", amount, sender)
    return jsonify({"message": f"Transferred ₹{amount:.2f} to {receiver}"}), 200

# --- Transaction History ---
@app.route("/history/<username>")
def history(username):
    txns = db.child("transactions").get().val()
    user_txns = [t for t in txns.values() if t["user"] == username] if txns else []
    return jsonify({"transactions": user_txns})

# --- Account Balance ---
@app.route("/balance/<username>")
def balance(username):
    acc = db.child("accounts").child(username).get().val()
    if not acc:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"balance": acc["balance"]})

# ------------------- RUN APP -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
