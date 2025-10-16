import os
import time
import hashlib
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate("bank-management-system-a0944-firebase-adminsdk-fbsvc-290ad1ae1a.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def create_account():
    user = input("Username: ").strip()
    if db.collection("accounts").document(user).get().exists:
        print("Username exists.")
        return
    fname = input("First name: ").strip()
    lname = input("Last name: ").strip()
    password = input("Password: ").strip()
    phone = input("Phone (10): ").strip()
    aadhar = input("Aadhar (12): ").strip()
    pass_hash = hashlib.sha256(password.encode()).hexdigest()
    db.collection("accounts").document(user).set({
        "fname": fname,
        "lname": lname,
        "pass_hash": pass_hash,
        "phone": phone,
        "aadhar": aadhar,
        "balance": 0.0
    })
    print("Account created.")

def login():
    user = input("Username: ").strip()
    password = input("Password: ").strip()
    doc = db.collection("accounts").document(user).get()
    if doc.exists and doc.to_dict()["pass_hash"] == hashlib.sha256(password.encode()).hexdigest():
        return user
    print("Invalid credentials.")
    return None

def deposit(user):
    amt = float(input("Amount to deposit: "))
    ref = db.collection("accounts").document(user)
    doc = ref.get()
    if doc.exists:
        balance = doc.to_dict()["balance"] + amt
        ref.update({"balance": balance})
        db.collection("txns").add({
            "user": user,
            "type": "deposit",
            "amount": amt,
            "other": "N/A",
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "id": f"{int(time.time())}{os.getpid()}"
        })
        print(f"Deposited. New balance: {balance:.2f}")

def withdraw(user):
    amt = float(input("Amount to withdraw: "))
    ref = db.collection("accounts").document(user)
    doc = ref.get()
    if doc.exists:
        balance = doc.to_dict()["balance"]
        if balance < amt:
            print("Insufficient funds.")
            return
        ref.update({"balance": balance - amt})
        db.collection("txns").add({
            "user": user,
            "type": "withdraw",
            "amount": amt,
            "other": "N/A",
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "id": f"{int(time.time())}{os.getpid()}"
        })
        print(f"Withdrawn. New balance: {balance - amt:.2f}")

def transfer(user):
    to = input("To (username): ").strip()
    amt = float(input("Amount: "))
    ref_from = db.collection("accounts").document(user)
    ref_to = db.collection("accounts").document(to)
    doc_from = ref_from.get()
    doc_to = ref_to.get()
    if not doc_to.exists:
        print("Recipient not found.")
        return
    balance = doc_from.to_dict()["balance"]
    if balance < amt:
        print("Insufficient funds.")
        return
    ref_from.update({"balance": balance - amt})
    ref_to.update({"balance": doc_to.to_dict()["balance"] + amt})
    txn_id = f"{int(time.time())}{os.getpid()}"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.collection("txns").add({
        "user": user,
        "type": "transfer_to",
        "amount": amt,
        "other": to,
        "time": timestamp,
        "id": txn_id
    })
    db.collection("txns").add({
        "user": to,
        "type": "transfer_from",
        "amount": amt,
        "other": user,
        "time": timestamp,
        "id": txn_id
    })
    print(f"Transferred {amt:.2f} to {to}. New balance: {balance - amt:.2f}")

def history(user):
    txns = db.collection("txns").where("user", "==", user).stream()
    print(f"{'S.No':<5} {'ID':<10} {'Type':<13} {'Amount':<8} {'Other':<10} {'Time'}")
    print("-" * 60)
    for i, t in enumerate(txns, 1):
        data = t.to_dict()
        print(f"{i:<5} {data['id']:<10} {data['type']:<13} {data['amount']:<8.2f} {data['other']:<10} {data['time']}")

def update_account(user):
    ref = db.collection("accounts").document(user)
    doc = ref.get()
    if doc.exists:
        acc = doc.to_dict()
        fname = input(f"First name ({acc['fname']}): ").strip()
        phone = input(f"Phone ({acc['phone']}): ").strip()
        updates = {}
        if fname: updates["fname"] = fname
        if phone: updates["phone"] = phone
        if updates:
            ref.update(updates)
            print("Updated.")

def delete_account(user):
    confirm = input("Confirm delete (y/N): ").strip().lower()
    if confirm == 'y':
        db.collection("accounts").document(user).delete()
        print("Deleted.")
        return True
    print("Aborted.")
    return False

def show_menu(user):
    while True:
        print(f"\nLogged in as: {user}")
        print("1) Balance  2) Deposit  3) Withdraw  4) Transfer")
        print("5) History  6) Update   7) Delete account  8) Logout")
        ch = input("Choice: ").strip()
        if ch == '1':
            doc = db.collection("accounts").document(user).get()
            if doc.exists:
                print(f"Balance: {doc.to_dict()['balance']:.2f}")
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
            if delete_account(user): break
        elif ch == '8':
            break

def main():
    while True:
        print("\n--- SIMPLE BANK ---")
        print("1) Create account\n2) Login\n3) Quit")
        ch = input("Choice: ").strip()
        if ch == '1':
            create_account()
        elif ch == '2':
            user = login()
            if user:
                show_menu(user)
        elif ch == '3':
            break

if __name__ == "__main__":
    main()
