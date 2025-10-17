from flask import Flask, jsonify, request, redirect, url_for
import threading
import time
import main as bank

app = Flask(__name__)

# Run the CLI in a background thread only when needed
_cli_thread = None

@app.route('/')
def index():
    return "Simple Cloud Bank - running"

@app.route('/health')
def health():
    return jsonify({'status':'ok'})

@app.route('/start_cli')
def start_cli():
    global _cli_thread
    if _cli_thread is None or not _cli_thread.is_alive():
        _cli_thread = threading.Thread(target=bank.main, daemon=True)
        _cli_thread.start()
        return jsonify({'started': True})
    return jsonify({'started': False, 'reason': 'already running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
