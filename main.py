import sys
import os

# If we're not running inside a virtualenv, try to switch into the project's .venv.
# This makes running the script with the system Python (e.g. /opt/homebrew/bin/python3)
# automatically use the project's virtualenv so required packages are available.
def ensure_venv_and_reexec():
    # Detect active venv
    in_venv = (hasattr(sys, 'real_prefix') or getattr(sys, 'base_prefix', None) != getattr(sys, 'prefix', None)
               or os.environ.get('VIRTUAL_ENV'))
    if in_venv:
        return

    project_root = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(project_root, '.venv', 'bin', 'python')

    if os.path.exists(venv_python):
        # Re-exec into .venv Python
        try:
            os.execv(venv_python, [venv_python] + sys.argv)
        except Exception:
            # If exec fails, let the import raise a clear error below
            return

    # Don't attempt to auto-create venv here (can fail on some systems).
    print('\nProject virtualenv not found. Please run:\n')
    print('  ./run.sh')
    print('\nor create and activate a virtualenv and install requirements:\n')
    print('  python3 -m venv .venv')
    print('  .venv/bin/python -m pip install -r requirements.txt\n')
    # Exit so we don't continue with missing dependencies
    sys.exit(1)


ensure_venv_and_reexec()

import pyrebase
import hashlib
import time
import json
from datetime import datetime
import getpass
import os
import random

# ------------------- CONFIGURE FIREBASE -------------------
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

# ------------------- UTILITIES -------------------

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def simple_hash(s):
    """Simple hash (like djb2 style)."""
    h = 5381
    for c in s:
        h = ((h << 5) + h) + ord(c)
    return str(h)

def pause(msg="\nPress Enter to continue..."):
    input(msg)

# ------------------- ACCOUNT OPS -------------------
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

# ---------------- Operations ----------------

def create_account():
    clear_screen()
    print("---- Create Account ----")
    fname = input("First name : ").strip()
    lname = input("Last name  : ").strip()
    user = input("Username   : ").strip()

    if find_account(user):
        print("❌ Username already exists.")
        pause()
        return

    password = getpass.getpass("Password: ")
    phone = input("Phone(10)  : ").strip()
    aadhar = input("Aadhar(12) : ").strip()

    acc = {
        "user": user,
        "pass_hash": simple_hash(password),
        "fname": fname,
        "lname": lname,
        "phone": phone,
        "aadhar": aadhar,
        "balance": 0.0
    }

    save_account(acc)
    print("✅ Account created successfully!")
    pause()

def login_prompt():
    clear_screen()
    print("---- Login ----")
    user = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    acc = find_account(user)
    if not acc:
        print("❌ No such user.")
        pause()
        return None

    if acc["pass_hash"] == simple_hash(password):
        print("✅ Login successful.")
        time.sleep(1)
        return user
    else:
        print("❌ Invalid password.")
        pause()
        return None

def deposit(username):
    try:
        amt = float(input("Amount to deposit: "))
        if amt <= 0:
            raise ValueError
    except ValueError:
        print("❌ Invalid amount.")
        time.sleep(1)
        return

    acc = find_account(username)
    acc["balance"] += amt
    db.child("accounts").child(username).update({"balance": acc["balance"]})
    append_txn(username, "deposit", amt)
    print(f"✅ Deposited ₹{amt:.2f}. New balance: ₹{acc['balance']:.2f}")
    time.sleep(1)

def withdraw(username):
    try:
        amt = float(input("Amount to withdraw: "))
        if amt <= 0:
            raise ValueError
    except ValueError:
        print("❌ Invalid amount.")
        time.sleep(1)
        return

    acc = find_account(username)
    if acc["balance"] < amt:
        print("❌ Insufficient funds.")
        time.sleep(1)
        return

    acc["balance"] -= amt
    db.child("accounts").child(username).update({"balance": acc["balance"]})
    append_txn(username, "withdraw", amt)
    print(f"✅ Withdrawn ₹{amt:.2f}. New balance: ₹{acc['balance']:.2f}")
    time.sleep(1)

def transfer(username):
    to_user = input("Transfer to username: ").strip()
    try:
        amt = float(input("Amount: "))
        if amt <= 0:
            raise ValueError
    except ValueError:
        print("❌ Invalid amount.")
        time.sleep(1)
        return

    receiver = find_account(to_user)
    if not receiver:
        print("❌ Recipient not found.")
        time.sleep(1)
        return

    sender = find_account(username)
    if sender["balance"] < amt:
        print("❌ Insufficient funds.")
        time.sleep(1)
        return

    # Update balances
    sender["balance"] -= amt
    receiver["balance"] += amt
    db.child("accounts").child(username).update({"balance": sender["balance"]})
    db.child("accounts").child(to_user).update({"balance": receiver["balance"]})

    # Record transactions
    append_txn(username, "transfer_to", amt, to_user)
    append_txn(to_user, "transfer_from", amt, username)
    print(f"✅ Transferred ₹{amt:.2f} to {to_user}.")
    time.sleep(1)

def history(username):
    clear_screen()
    txns = db.child("transactions").get().val()
    print(f"{'ID':<15}{'Type':<15}{'Amount':<10}{'Other':<15}{'Time'}")
    print("-" * 70)
    if txns:
        for t in txns.values():
            if t["user"] == username:
                print(f"{t['id']:<15}{t['type']:<15}{t['amount']:<10.2f}{t['other']:<15}{t['time']}")
    else:
        print("No transactions.")
    input("\nPress Enter to continue...")

def update_account(username):
    acc = find_account(username)
    print(f"First name ({acc['fname']}): ", end="")
    new_fname = input().strip()
    if new_fname:
        acc["fname"] = new_fname
    print(f"Phone ({acc['phone']}): ", end="")
    new_phone = input().strip()
    if new_phone:
        acc["phone"] = new_phone
    save_account(acc)
    print("✅ Account updated.")
    time.sleep(1)

def delete_account(username):
    confirm = input("Confirm delete (y/N): ").lower()
    if confirm != 'y':
        print("Aborted.")
        time.sleep(1)
        return False
    db.child("accounts").child(username).remove()
    print("✅ Account deleted.")
    time.sleep(1)
    return True

# ---------------- Menu ----------------

def show_menu(user):
    while True:
        clear_screen()
        print(f"Logged in as: {user}\n")
        print("1) Balance\n2) Deposit\n3) Withdraw\n4) Transfer")
        print("5) History\n6) Update\n7) Delete account\n8) Logout")
        ch = input("Choice: ").strip()
        if ch == '1':
            acc = find_account(user)
            print(f"Balance: ₹{acc['balance']:.2f}")
            pause()
        elif ch == '2':
            deposit(user)
        elif ch == '3':
            withdraw(user)
        elif ch == '4':
            transfer(user)
        elif ch == '5':
            history(user)
        elif ch == '6':
            update_account(user)
        elif ch == '7':
            if delete_account(user):
                return
        elif ch == '8':
            return

# ------------------- MAIN -------------------
def main():
    while True:
        clear_screen()
        print("--- SIMPLE BANK ---")
        print("1) Create account")
        print("2) Login")
        print("3) Quit")
        ch = input("Choice: ").strip()
        if ch == '1':
            create_account()
        elif ch == '2':
            user = login_prompt()
            if user:
                show_menu(user)
        elif ch == '3':
            print("Exiting...")
            time.sleep(0.5)
            break

if __name__ == "__main__":
    main()
