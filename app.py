from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from detoxify import Detoxify
import hashlib
import json
import os
from datetime import datetime
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pytesseract
from PIL import Image
import io
import base64
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Flask-Mail setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_password'  # Replace with your password
mail = Mail(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
# Database setup
DATABASE = 'evidence.db'
DATABASE = os.environ.get('DB_PATH', 'evidence.db')
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT UNIQUE,
            message TEXT,
            category TEXT,
            severity TEXT,
            hash TEXT,
            timestamp TEXT,
            image_path TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS blockchain_anchors (
            evidence_id TEXT PRIMARY KEY,
            block_hash TEXT,
            anchored_at TEXT
        )''')
        # Insert default user
        db.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', 'password')")
        db.commit()

init_db()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user['id'], user['username'])
    return None

# Load Detoxify model
model = Detoxify('original')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        if user:
            login_user(User(user['id'], user['username']))
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    db = get_db()
    cursor = db.execute('SELECT severity, COUNT(*) as count FROM evidence GROUP BY severity')
    stats = {row['severity']: row['count'] for row in cursor.fetchall()}
    total = sum(stats.values())
    return render_template('index.html', stats=stats, total=total)

@app.route('/vault')
@login_required
def vault():
    db = get_db()
    cursor = db.execute('SELECT * FROM evidence ORDER BY timestamp DESC')
    records = cursor.fetchall()
    return render_template('vault.html', records=records)

@app.route('/legal/<evidence_id>')
def legal(evidence_id):
    db = get_db()
    cursor = db.execute('SELECT * FROM evidence WHERE evidence_id = ?', (evidence_id,))
    record = cursor.fetchone()
    if not record:
        return "Record not found", 404
    
    # Generate PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, f"Evidence ID: {record['evidence_id']}")
    c.drawString(100, 730, f"Message: {record['message']}")
    c.drawString(100, 710, f"Category: {record['category']}")
    c.drawString(100, 690, f"Severity: {record['severity']}")
    c.drawString(100, 670, f"Hash: {record['hash']}")
    c.drawString(100, 650, f"Timestamp: {record['timestamp']}")
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{evidence_id}.pdf", mimetype='application/pdf')

@app.route('/detect', methods=['POST'])
def detect():
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Detect toxicity
    results = model.predict(message)
    
    # Determine category and severity
    categories = ['toxicity', 'severe_toxicity', 'obscene', 'threat', 'insult', 'identity_hate']
    max_score = max(results[cat] for cat in categories)
    category = max(categories, key=lambda x: results[x])
    
    if max_score > 0.8:
        severity = 'High'
    elif max_score > 0.5:
        severity = 'Medium'
    else:
        severity = 'Low'
    
    # Generate evidence ID and hash
    timestamp = datetime.utcnow().isoformat()
    evidence_id = hashlib.sha256((message + timestamp).encode()).hexdigest()[:16]
    hash_value = hashlib.sha256((message + category + severity + timestamp).encode()).hexdigest()
    
    # Store in DB
    db = get_db()
    db.execute('INSERT INTO evidence (evidence_id, message, category, severity, hash, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
               (evidence_id, message, category, severity, hash_value, timestamp))
    db.commit()
    
    # Send email alert for high severity
    if severity == 'High':
        msg = Message('High Severity Cyberbullying Detected', sender='your_email@gmail.com', recipients=['alert@example.com'])
        msg.body = f"Evidence ID: {evidence_id}\nMessage: {message}\nCategory: {category}\nSeverity: {severity}"
        mail.send(msg)
    
    return jsonify({
        'evidence_id': evidence_id,
        'category': category,
        'severity': severity,
        'hash': hash_value,
        'timestamp': timestamp
    })

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file
    filename = hashlib.sha256(file.read()).hexdigest() + os.path.splitext(file.filename)[1]
    file.seek(0)
    filepath = os.path.join('uploads', filename)
    file.save(filepath)
    
    # Extract text using OCR
    image = Image.open(filepath)
    text = pytesseract.image_to_string(image)
    
    # Detect on extracted text
    if text.strip():
        return detect_text(text, filepath)
    else:
        return jsonify({'error': 'No text found in image'}), 400

def detect_text(message, image_path):
    results = model.predict(message)
    
    categories = ['toxicity', 'severe_toxicity', 'obscene', 'threat', 'insult', 'identity_hate']
    max_score = max(results[cat] for cat in categories)
    category = max(categories, key=lambda x: results[x])
    
    if max_score > 0.8:
        severity = 'High'
    elif max_score > 0.5:
        severity = 'Medium'
    else:
        severity = 'Low'
    
    timestamp = datetime.utcnow().isoformat()
    evidence_id = hashlib.sha256((message + timestamp).encode()).hexdigest()[:16]
    hash_value = hashlib.sha256((message + category + severity + timestamp + image_path).encode()).hexdigest()
    
    db = get_db()
    db.execute('INSERT INTO evidence (evidence_id, message, category, severity, hash, timestamp, image_path) VALUES (?, ?, ?, ?, ?, ?, ?)',
               (evidence_id, message, category, severity, hash_value, timestamp, image_path))
    db.commit()
    
    # Send email alert for high severity
    if severity == 'High':
        msg = Message('High Severity Cyberbullying Detected', sender='your_email@gmail.com', recipients=['alert@example.com'])
        msg.body = f"Evidence ID: {evidence_id}\nMessage: {message}\nCategory: {category}\nSeverity: {severity}"
        mail.send(msg)
    
    return jsonify({
        'evidence_id': evidence_id,
        'category': category,
        'severity': severity,
        'hash': hash_value,
        'timestamp': timestamp,
        'text': message
    })

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    severity = request.args.get('severity', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    db = get_db()
    sql = 'SELECT * FROM evidence WHERE 1=1'
    params = []
    
    if query:
        sql += ' AND (message LIKE ? OR evidence_id LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%'])
    
    if severity:
        sql += ' AND severity = ?'
        params.append(severity)
    
    if date_from:
        sql += ' AND timestamp >= ?'
        params.append(date_from)
    
    if date_to:
        sql += ' AND timestamp <= ?'
        params.append(date_to + 'T23:59:59')
    
    sql += ' ORDER BY timestamp DESC'
    cursor = db.execute(sql, params)
    records = cursor.fetchall()
    
    return jsonify([dict(record) for record in records])

@app.route('/chart_data')
def chart_data():
    db = get_db()
    cursor = db.execute('SELECT strftime("%Y-%m", timestamp) as month, severity, COUNT(*) as count FROM evidence GROUP BY month, severity ORDER BY month')
    data = cursor.fetchall()
    
    months = []
    high = []
    medium = []
    low = []
    
    for row in data:
        month = row['month']
        if month not in months:
            months.append(month)
            high.append(0)
            medium.append(0)
            low.append(0)
        
        idx = months.index(month)
        if row['severity'] == 'High':
            high[idx] = row['count']
        elif row['severity'] == 'Medium':
            medium[idx] = row['count']
        else:
            low[idx] = row['count']
    
    return jsonify({
        'months': months,
        'high': high,
        'medium': medium,
        'low': low
    })

@app.route('/anchor/<evidence_id>')
@login_required
def anchor(evidence_id):
    db = get_db()
    cursor = db.execute('SELECT * FROM evidence WHERE evidence_id = ?', (evidence_id,))
    record = cursor.fetchone()
    if not record:
        return "Record not found", 404
    
    # Mock blockchain anchoring
    # In real implementation, send to blockchain API
    block_hash = hashlib.sha256((record['hash'] + str(datetime.utcnow())).encode()).hexdigest()
    
    # Store anchor info
    db.execute('INSERT OR REPLACE INTO blockchain_anchors (evidence_id, block_hash, anchored_at) VALUES (?, ?, ?)',
               (evidence_id, block_hash, datetime.utcnow().isoformat()))
    db.commit()
    
    flash(f"Evidence {evidence_id} anchored on blockchain with hash {block_hash}")
    return redirect(url_for('vault'))

if __name__ == '__main__':
    app.run(debug=True)
