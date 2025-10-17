
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")
from flask import Flask, jsonify, request
import main as bank

app = Flask(__name__)

@app.route('/')
def index():
    return "Simple Cloud Bank API - running"

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.json
    required = ['fname', 'lname', 'user', 'password', 'phone', 'aadhar']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing fields'}), 400
    if bank.find_account(data['user']):
        return jsonify({'error': 'Username already exists'}), 409
    acc = {
        "user": data['user'],
        "pass_hash": bank.simple_hash(data['password']),
        "fname": data['fname'],
        "lname": data['lname'],
        "phone": data['phone'],
        "aadhar": data['aadhar'],
        "balance": 0.0
    }
    bank.save_account(acc)
    return jsonify({'success': True})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = data.get('user')
    password = data.get('password')
    acc = bank.find_account(user)
    if not acc:
        return jsonify({'error': 'No such user'}), 404
    if acc['pass_hash'] != bank.simple_hash(password):
        return jsonify({'error': 'Incorrect password'}), 401
    return jsonify({'success': True, 'user': user})

@app.route('/deposit', methods=['POST'])
def deposit():
    data = request.json
    user = data.get('user')
    amt = data.get('amount')
    acc = bank.find_account(user)
    if not acc:
        return jsonify({'error': 'No such user'}), 404
    try:
        amt = float(amt)
        if amt <= 0:
            raise ValueError
    except Exception:
        return jsonify({'error': 'Invalid amount'}), 400
    acc['balance'] += amt
    bank.save_account(acc)
    bank.append_txn(user, 'deposit', amt)
    return jsonify({'success': True, 'balance': acc['balance']})

@app.route('/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    user = data.get('user')
    amt = data.get('amount')
    acc = bank.find_account(user)
    if not acc:
        return jsonify({'error': 'No such user'}), 404
    try:
        amt = float(amt)
        if amt <= 0:
            raise ValueError
    except Exception:
        return jsonify({'error': 'Invalid amount'}), 400
    if acc['balance'] < amt:
        return jsonify({'error': 'Insufficient funds'}), 400
    acc['balance'] -= amt
    bank.save_account(acc)
    bank.append_txn(user, 'withdraw', amt)
    return jsonify({'success': True, 'balance': acc['balance']})

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.json
    user = data.get('user')
    to_user = data.get('to_user')
    amt = data.get('amount')
    sender = bank.find_account(user)
    receiver = bank.find_account(to_user)
    if not sender or not receiver:
        return jsonify({'error': 'User not found'}), 404
    try:
        amt = float(amt)
        if amt <= 0:
            raise ValueError
    except Exception:
        return jsonify({'error': 'Invalid amount'}), 400
    if sender['balance'] < amt:
        return jsonify({'error': 'Insufficient funds'}), 400
    sender['balance'] -= amt
    receiver['balance'] += amt
    bank.save_account(sender)
    bank.save_account(receiver)
    bank.append_txn(user, 'transfer_to', amt, to_user)
    bank.append_txn(to_user, 'transfer_from', amt, user)
    return jsonify({'success': True, 'balance': sender['balance']})

@app.route('/history/<user>', methods=['GET'])
def history(user):
    txns = bank.db.child('transactions').get().val()
    result = []
    if txns:
        for t in txns.values():
            if t['user'] == user:
                result.append(t)
    return jsonify({'transactions': result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
