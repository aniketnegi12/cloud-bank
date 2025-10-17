from flask import Flask, render_template, request, redirect, url_for
import pyrebase
import hashlib
import time
import random
from datetime import datetime
import os

app = Flask(__name__)

# ------------------- CONFIGURE FIREBASE -------------------
firebaseConfig = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "YOUR_AUTH_DOMAIN",
    "databaseURL": "YOUR_DATABASE_URL",
    "projectId": "YOUR_PROJECT_ID",
    "storageBucket": "YOUR_STORAGE_BUCKET",
    "messagingSenderId": "YOUR_SENDER_ID",
    "appId": "YOUR_APP_ID"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

# ------------------- UTILITIES -------------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def simple_hash(s):
    """Simple hash for password."""
    return hashlib.sha256(s.encode()).hexdigest()

def find_account(username):
    return db.child("accounts").child(username).get().val()

def save_account(acc):
    db.child("accounts").child(acc["user"]).set(acc)

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

# ------------------- ROUTES -------------------

@app.route("/")
def home():
    return render_template("index.html")

# ---------- Signup ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        fname = request.form.get("fname").strip()
        lname = request.form.get("lname").strip()
        username = request.form.get("username").strip()
        password = request.form.get("password")
        phone = request.form.get("phone").strip()
        aadhar = request.form.get("aadhar").strip()

        if find_account(username):
            error = "Username already exists!"
        else:
            acc = {
                "fname": fname,
                "lname": lname,
                "user": username,
                "pass_hash": simple_hash(password),
                "phone": phone,
                "aadhar": aadhar,
                "balance": 0.0
            }
            save_account(acc)
            return redirect(url_for("login"))
    return render_template("signup.html", error=error)

# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        acc = find_account(username)
        if not acc:
            error = "User not found!"
        elif acc["pass_hash"] != simple_hash(password):
            error = "Incorrect password!"
        else:
            return redirect(url_for("dashboard", username=username))
    return render_template("login.html", error=error)

# ---------- Dashboard ----------
@app.route("/dashboard/<username>")
def dashboard(username):
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))
    return render_template("dashboard.html", account=acc)

# ---------- Deposit ----------
@app.route("/deposit/<username>", methods=["GET", "POST"])
def deposit(username):
    error = success = None
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            amt = float(request.form.get("amount"))
            if amt <= 0:
                raise ValueError
            acc["balance"] += amt
            db.child("accounts").child(username).update({"balance": acc["balance"]})
            append_txn(username, "deposit", amt)
            success = f"Deposited ₹{amt:.2f} successfully!"
        except:
            error = "Invalid amount!"
    return render_template("deposit.html", username=username, error=error, success=success, balance=acc["balance"])

# ---------- Withdraw ----------
@app.route("/withdraw/<username>", methods=["GET", "POST"])
def withdraw(username):
    error = success = None
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            amt = float(request.form.get("amount"))
            if amt <= 0 or amt > acc["balance"]:
                raise ValueError
            acc["balance"] -= amt
            db.child("accounts").child(username).update({"balance": acc["balance"]})
            append_txn(username, "withdraw", amt)
            success = f"Withdrawn ₹{amt:.2f} successfully!"
        except:
            error = "Invalid amount or insufficient funds!"
    return render_template("withdraw.html", username=username, error=error, success=success, balance=acc["balance"])

# ---------- Transfer ----------
@app.route("/transfer/<username>", methods=["GET", "POST"])
def transfer(username):
    error = success = None
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))

    if request.method == "POST":
        to_user = request.form.get("to_user").strip()
        try:
            amt = float(request.form.get("amount"))
            if amt <= 0 or amt > acc["balance"]:
                raise ValueError
            receiver = find_account(to_user)
            if not receiver:
                raise ValueError("Recipient not found")
            # Update balances
            acc["balance"] -= amt
            receiver["balance"] += amt
            db.child("accounts").child(username).update({"balance": acc["balance"]})
            db.child("accounts").child(to_user).update({"balance": receiver["balance"]})
            append_txn(username, "transfer_to", amt, to_user)
            append_txn(to_user, "transfer_from", amt, username)
            success = f"Transferred ₹{amt:.2f} to {to_user}!"
        except:
            error = "Invalid transfer!"
    return render_template("transfer.html", username=username, error=error, success=success, balance=acc["balance"])

# ---------- History ----------
@app.route("/history/<username>")
def history(username):
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))
    all_txns = db.child("transactions").get().val()
    txns = [t for t in all_txns.values() if t["user"]==username] if all_txns else []
    return render_template("history.html", transactions=txns, username=username)

# ---------- Run App ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)
