from firebase_config import db
from datetime import datetime
import hashlib

def simple_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ✅ Create account
def create_account(username, password, fname, lname, phone, aadhar):
    acc_ref = db.collection("accounts").document(username)
    acc_data = {
        "username": username,
        "password_hash": simple_hash(password),
        "fname": fname,
        "lname": lname,
        "phone": phone,
        "aadhar": aadhar,
        "balance": 0.0,
        "created_at": datetime.now().isoformat()
    }
    acc_ref.set(acc_data)
    print("✅ Account created successfully!")

# ✅ Login
def login(username, password):
    acc_ref = db.collection("accounts").document(username).get()
    if acc_ref.exists:
        acc = acc_ref.to_dict()
        if acc["password_hash"] == simple_hash(password):
            print("✅ Login successful!")
            return username
    print("❌ Invalid credentials.")
    return None

# ✅ Deposit
def deposit(username, amount):
    ref = db.collection("accounts").document(username)
    acc = ref.get().to_dict()
    acc["balance"] += amount
    ref.update({"balance": acc["balance"]})
    print(f"💰 Deposited {amount}. New balance: {acc['balance']}")

# ✅ Withdraw
def withdraw(username, amount):
    ref = db.collection("accounts").document(username)
    acc = ref.get().to_dict()
    if acc["balance"] < amount:
        print("❌ Insufficient funds.")
        return
    acc["balance"] -= amount
    ref.update({"balance": acc["balance"]})
    print(f"💸 Withdrawn {amount}. New balance: {acc['balance']}")

# ✅ Transfer
def transfer(sender, receiver, amount):
    sender_ref = db.collection("accounts").document(sender)
    receiver_ref = db.collection("accounts").document(receiver)
    s_acc = sender_ref.get().to_dict()
    r_acc = receiver_ref.get().to_dict()
    if s_acc["balance"] < amount:
        print("❌ Insufficient funds.")
        return
    s_acc["balance"] -= amount
    r_acc["balance"] += amount
    sender_ref.update({"balance": s_acc["balance"]})
    receiver_ref.update({"balance": r_acc["balance"]})
    print(f"✅ Transferred {amount} from {sender} to {receiver}")

# ✅ Show Balance
def show_balance(username):
    ref = db.collection("accounts").document(username)
    acc = ref.get().to_dict()
    print(f"💵 Current balance: {acc['balance']}")
