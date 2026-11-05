from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from suava import SuavaChain, Wallet, Transaction
from dataclasses import asdict
import json
import os

app = Flask(__name__)
app.secret_key = "suava_super_secret_key" 

s = SuavaChain()
network_faucet = "00000000000000000000"
USERS_FILE = "users.json"

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users_db = json.load(f)
else:
    users_db = {}

def load_user_wallet(username):
    if username in users_db:
        w = Wallet(username)
        w.private_key = users_db[username]["private_key"]
        w.public_key = users_db[username]["public_key"]
        return w
    return None

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in users_db:
        return jsonify({"message": "❌ Username already exists!"})

    new_wallet = Wallet(username)
    users_db[username] = {
        "password": password,
        "private_key": new_wallet.private_key,
        "public_key": new_wallet.public_key
    }
    
    with open(USERS_FILE, "w") as f:
        json.dump(users_db, f, indent=4)

    return jsonify({"message": f"✅ Wallet created for {username}! Please login."})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username not in users_db or users_db[username]['password'] != password:
        return jsonify({"message": "❌ Invalid username or password."})

    session['user'] = username
    return jsonify({"message": "✅ Login successful!"})

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    user_wallet = load_user_wallet(session['user'])
    balance = s.get_balance(user_wallet.public_key)
    
    history = []
    for block in s.chain:
        for tx in block.transactions:
            if tx.sender_public_key == user_wallet.public_key:
                history.append(f"Sent {tx.amount} SVA to {tx.receiver_public_key[:10]}...")
            elif tx.receiver_public_key == user_wallet.public_key:
                if tx.sender_public_key == network_faucet:
                    history.append(f"Mining Reward: +{tx.amount} SVA")
                else:
                    history.append(f"Received {tx.amount} SVA from {tx.sender_public_key[:10]}...")
                    
    return render_template('dashboard.html', username=session['user'], balance=balance, address=user_wallet.public_key, history=history[::-1])

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/mine', methods=['POST'])
def mine():
    if 'user' not in session:
        return jsonify({"message": "Not logged in"})
        
    user_wallet = load_user_wallet(session['user'])
    reward_tx = Transaction(network_faucet, user_wallet.public_key, 50.0, "MINING_REWARD")
    s.add_tx(reward_tx)
    s.mine_block()
    s.save_to_disk()
    return jsonify({"message": "Block Mined! You earned 50 SVA."})

@app.route('/send', methods=['POST'])
def send():
    if 'user' not in session:
        return jsonify({"message": "Not logged in"})

    data = request.json
    receiver = data.get('receiver')
    amount = float(data.get('amount'))
    
    user_wallet = load_user_wallet(session['user'])
    
    if s.get_balance(user_wallet.public_key) >= amount:
        sig = user_wallet.sign_transaction(receiver, amount)
        tx = Transaction(user_wallet.public_key, receiver, amount, sig)
        s.add_tx(tx)
        s.mine_block()
        s.save_to_disk()
        return jsonify({"message": f"Sent {amount} SVA!"})
    else:
        return jsonify({"message": "Insufficient funds!"})

@app.route('/founder_claim', methods=['POST'])
def founder_claim():
    if 'user' not in session:
        return jsonify({"message": "Not logged in"})
        
    user_wallet = load_user_wallet(session['user'])
    
    current_balance = s.get_balance(user_wallet.public_key)
    if current_balance >= 2000000.0:
        return jsonify({"message": "You already claimed your Founder's reward!"})

    airdrop_tx = Transaction(network_faucet, user_wallet.public_key, 2000000.0, "FOUNDER_SIG")
    s.add_tx(airdrop_tx)
    s.mine_block()
    s.save_to_disk()
    
    return jsonify({"message": "👑 Founder's Allocation of 2,000,000 SVA claimed!"})

if __name__ == '__main__':
    app.run(debug=True)