import pyrebase
import hashlib
import time
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
    os.system("cls" if os.name == "nt" else "clear")

def simple_hash(s):
    return hashlib.sha256(s.encode()).hexdigest()

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ------------------- ACCOUNT OPS -------------------
def create_account():
    clear_screen()
    print("--- CREATE ACCOUNT ---")
    fname = input("First name: ").strip()
    lname = input("Last name : ").strip()
    username = input("Username  : ").strip()
    user_ref = db.child("accounts").child(username).get()

    if user_ref.val():
        print("❌ Username already exists.")
        time.sleep(1)
        return

    password = getpass.getpass("Password  : ")
    phone = input("Phone(10) : ").strip()
    aadhar = input("Aadhar(12): ").strip()

    data = {
        "fname": fname,
        "lname": lname,
        "user": username,
        "pass_hash": simple_hash(password),
        "phone": phone,
        "aadhar": aadhar,
        "balance": 0.0
    }
    db.child("accounts").child(username).set(data)
    print("✅ Account created successfully!")
    time.sleep(1)


def login():
    clear_screen()
    print("--- LOGIN ---")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    acc = db.child("accounts").child(username).get().val()
    if not acc:
        print("❌ No such user.")
        time.sleep(1)
        return None

    if acc["pass_hash"] != simple_hash(password):
        print("❌ Incorrect password.")
        time.sleep(1)
        return None

    print(f"✅ Welcome, {acc['fname']}!")
    time.sleep(1)
    return acc


# ------------------- TRANSACTIONS -------------------
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


def deposit(acc):
    amt = float(input("Amount to deposit: "))
    acc["balance"] += amt
    db.child("accounts").child(acc["user"]).update({"balance": acc["balance"]})
    append_txn(acc["user"], "deposit", amt)
    print(f"Deposited ₹{amt:.2f}. New balance: ₹{acc['balance']:.2f}")
    time.sleep(1)


def withdraw(acc):
    amt = float(input("Amount to withdraw: "))
    if acc["balance"] < amt:
        print("❌ Insufficient funds.")
        return
    acc["balance"] -= amt
    db.child("accounts").child(acc["user"]).update({"balance": acc["balance"]})
    append_txn(acc["user"], "withdraw", amt)
    print(f"Withdrawn ₹{amt:.2f}. New balance: ₹{acc['balance']:.2f}")
    time.sleep(1)


def transfer(acc):
    to_user = input("Transfer to username: ").strip()
    amt = float(input("Amount: "))

    receiver = db.child("accounts").child(to_user).get().val()
    if not receiver:
        print("❌ Recipient not found.")
        return
    if acc["balance"] < amt:
        print("❌ Insufficient funds.")
        return

    # Update balances
    acc["balance"] -= amt
    receiver["balance"] += amt
    db.child("accounts").child(acc["user"]).update({"balance": acc["balance"]})
    db.child("accounts").child(to_user).update({"balance": receiver["balance"]})

    # Record transactions
    append_txn(acc["user"], "transfer_to", amt, to_user)
    append_txn(to_user, "transfer_from", amt, acc["user"])
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


# ------------------- MENU -------------------
def show_menu(acc):
    while True:
        clear_screen()
        print(f"--- Welcome, {acc['user']} ---")
        print("1) Balance\n2) Deposit\n3) Withdraw\n4) Transfer\n5) History\n6) Logout")
        ch = input("Choice: ").strip()
        if ch == '1':
            acc = db.child("accounts").child(acc["user"]).get().val()
            print(f"Balance: ₹{acc['balance']:.2f}")
            input("Press Enter...")
        elif ch == '2':
            deposit(acc)
        elif ch == '3':
            withdraw(acc)
        elif ch == '4':
            transfer(acc)
        elif ch == '5':
            history(acc["user"])
        elif ch == '6':
            return


# ------------------- MAIN -------------------
def main():
    while True:
        clear_screen()
        print("--- SIMPLE CLOUD BANK ---")
        print("1) Create Account")
        print("2) Login")
        print("3) Quit")
        choice = input("Choice: ").strip()
        if choice == '1':
            create_account()
        elif choice == '2':
            acc = login()
            if acc:
                show_menu(acc)
        elif choice == '3':
            break


if __name__ == "__main__":
    main()
