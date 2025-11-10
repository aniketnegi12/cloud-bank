from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyrebase
import hashlib
import time
import random
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

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
    s = s or ""
    return hashlib.sha256(s.encode()).hexdigest()

def find_account(username):
    if not username:
        return None
    return db.child("accounts").child(username).get().val()

def save_account(acc):
    db.child("accounts").child(acc["user"]).set(acc)

def append_txn(username, ttype, amount, other="N/A"):
    txn_id = f"{int(time.time())}{random.randint(1000,9999)}"
    txn = {
        "user": username,
        "type": ttype,
        "amount": float(amount),
        "other": other,
        "time": now_str(),
        "id": txn_id
    }
    db.child("transactions").push(txn)

# ------------------- ROUTES (UI) -------------------

@app.route("/")
def home():
    return render_template("index.html")

# Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        fname = (request.form.get("fname") or "").strip()
        lname = (request.form.get("lname") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        phone = (request.form.get("phone") or "").strip()
        aadhar = (request.form.get("aadhar") or "").strip()

        if not username or not password:
            error = "Username and password are required."
        elif find_account(username):
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
            flash("Account created. Please login.", "success")
            return redirect(url_for("login"))
    return render_template("signup.html", error=error)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        acc = find_account(username)
        if not acc:
            error = "User not found!"
        elif acc.get("pass_hash") != simple_hash(password):
            error = "Incorrect password!"
        else:
            session["username"] = username
            return redirect(url_for("dashboard", username=username))
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# Dashboard (username optional -> fallback to session)
@app.route("/dashboard")
@app.route("/dashboard/<username>")
def dashboard(username=None):
    if username is None:
        username = session.get("username")
    if not username:
        flash("Please login to access dashboard", "error")
        return redirect(url_for("login"))
    acc = find_account(username)
    if not acc:
        flash("Account not found", "error")
        return redirect(url_for("login"))
    # fetch recent txns for display
    all_txns = db.child("transactions").get().val()
    txns = [t for t in all_txns.values() if t["user"] == username] if all_txns else []
    return render_template("dashboard.html", account=acc, transactions=txns, username=username)

# Deposit
@app.route("/deposit", methods=["GET", "POST"])
@app.route("/deposit/<username>", methods=["GET", "POST"])
def deposit(username=None):
    error = None
    if username is None:
        username = session.get("username")
    if not username:
        flash("Please login to deposit", "error")
        return redirect(url_for("login"))
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            amt = float(request.form.get("amount") or 0)
            if amt <= 0:
                raise ValueError
            acc["balance"] = float(acc.get("balance", 0)) + amt
            db.child("accounts").child(username).update({"balance": acc["balance"]})
            append_txn(username, "deposit", amt)
            flash(f"Deposited ₹{amt:.2f} successfully!", "success")
            return redirect(url_for("dashboard", username=username))
        except Exception:
            error = "Invalid amount!"
    return render_template("deposit.html", username=username, error=error, balance=acc.get("balance", 0.0))

# Withdraw
@app.route("/withdraw", methods=["GET", "POST"])
@app.route("/withdraw/<username>", methods=["GET", "POST"])
def withdraw(username=None):
    error = None
    if username is None:
        username = session.get("username")
    if not username:
        flash("Please login to withdraw", "error")
        return redirect(url_for("login"))
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))
    if request.method == "POST":
        try:
            amt = float(request.form.get("amount") or 0)
            if amt <= 0 or float(acc.get("balance", 0)) < amt:
                raise ValueError
            acc["balance"] = float(acc.get("balance", 0)) - amt
            db.child("accounts").child(username).update({"balance": acc["balance"]})
            append_txn(username, "withdraw", amt)
            flash(f"Withdrawn ₹{amt:.2f} successfully!", "success")
            return redirect(url_for("dashboard", username=username))
        except Exception:
            error = "Invalid amount or insufficient funds!"
    return render_template("withdraw.html", username=username, error=error, balance=acc.get("balance", 0.0))

# Transfer
@app.route("/transfer", methods=["GET", "POST"])
@app.route("/transfer/<username>", methods=["GET", "POST"])
def transfer(username=None):
    error = None
    if username is None:
        username = session.get("username")
    if not username:
        flash("Please login to transfer", "error")
        return redirect(url_for("login"))
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))
    if request.method == "POST":
        to_user = (request.form.get("to_user") or "").strip()
        try:
            amt = float(request.form.get("amount") or 0)
            if amt <= 0 or float(acc.get("balance", 0)) < amt:
                raise ValueError
            receiver = find_account(to_user)
            if not receiver:
                raise ValueError("Recipient not found")
            acc["balance"] = float(acc.get("balance", 0)) - amt
            receiver["balance"] = float(receiver.get("balance", 0)) + amt
            db.child("accounts").child(username).update({"balance": acc["balance"]})
            db.child("accounts").child(to_user).update({"balance": receiver["balance"]})
            append_txn(username, "transfer_to", amt, to_user)
            append_txn(to_user, "transfer_from", amt, username)
            flash(f"Transferred ₹{amt:.2f} to {to_user}!", "success")
            return redirect(url_for("dashboard", username=username))
        except Exception:
            error = "Invalid transfer!"
    return render_template("transfer.html", username=username, error=error, balance=acc.get("balance", 0.0))

# History
@app.route("/history")
@app.route("/history/<username>")
def history(username=None):
    if username is None:
        username = session.get("username")
    if not username:
        flash("Please login to view history", "error")
        return redirect(url_for("login"))
    acc = find_account(username)
    if not acc:
        return redirect(url_for("login"))
    all_txns = db.child("transactions").get().val()
    txns = [t for t in all_txns.values() if t["user"] == username] if all_txns else []
    return render_template("history.html", transactions=txns, username=username)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
