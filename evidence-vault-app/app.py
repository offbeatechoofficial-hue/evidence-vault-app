# app.py

from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
import os
import hashlib
import uuid
from datetime import datetime
from detoxify import Detoxify
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
app = Flask(__name__)
app.secret_key = "vault_secret"
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
DB_NAME = r"C:\Users\Payal\Documents\evidence.db"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- DATABASE ---------------- #
# app.py

from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import sqlite3
import os
import hashlib
import uuid
from datetime import datetime
from detoxify import Detoxify
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "vault_secret"

UPLOAD_FOLDER = "uploads"
DB_NAME = r"C:\Users\Payal\Documents\evidence.db"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_id TEXT,
        content TEXT,
        category TEXT,
        severity TEXT,
        score REAL,
        hash TEXT,
        filename TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- AI MODEL ---------------- #

model = Detoxify('original')

def detect_toxicity(text):
    result = model.predict(text)

    score = max(result.values())

    if score >= 0.80:
        severity = "High"
    elif score >= 0.50:
        severity = "Medium"
    else:
        severity = "Low"

    category = max(result, key=result.get)

    return category, severity, round(score, 2)

# ---------------- HASH ---------------- #

def generate_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

# ---------------- SAVE DATA ---------------- #

def save_record(evidence_id, content, category, severity, score, hash_val, filename):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO evidence
    (evidence_id, content, category, severity, score, hash, filename, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        evidence_id,
        content,
        category,
        severity,
        score,
        hash_val,
        filename,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

# ---------------- HOME ---------------- #

@app.route("/")
def home():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM evidence")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM evidence WHERE severity='High'")
    high = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM evidence WHERE severity='Medium'")
    medium = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM evidence WHERE severity='Low'")
    low = cur.fetchone()[0]

    conn.close()

    return render_template("index.html",
                           total=total,
                           high=high,
                           medium=medium,
                           low=low)

# ---------------- ANALYZE ---------------- #

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.form["message"]
    file = request.files.get("image")

    filename = ""

    if file and file.filename != "":
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    category, severity, score = detect_toxicity(text)

    evidence_id = str(uuid.uuid4())[:8].upper()
    hash_val = generate_hash(text + str(datetime.now()))

    save_record(evidence_id, text, category, severity, score, hash_val, filename)

    flash(f"Evidence Stored Successfully | Severity: {severity}")

    return redirect(url_for("vault"))

# ---------------- VAULT ---------------- #

@app.route("/vault")
def vault():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM evidence ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()

    return render_template("vault.html", records=data)

# ---------------- PDF REPORT ---------------- #

@app.route("/report/<evidence_id>")
def report(evidence_id):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,))
    row = cur.fetchone()

    conn.close()

    if not row:
        return "Not Found"

    filename = f"{evidence_id}_report.pdf"

    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(150, 800, "Cyberbullying Legal Evidence Report")

    c.setFont("Helvetica", 12)

    y = 760

    labels = [
        f"Evidence ID: {row[1]}",
        f"Message: {row[2]}",
        f"Category: {row[3]}",
        f"Severity: {row[4]}",
        f"Confidence Score: {row[5]}",
        f"SHA256 Hash: {row[6]}",
        f"Uploaded File: {row[7]}",
        f"Timestamp: {row[8]}"
    ]

    for item in labels:
        c.drawString(50, y, item[:110])
        y -= 30

    c.save()

    return send_file(filename, as_attachment=True)

# ---------------- LEGAL PAGE ---------------- #

@app.route("/legal")
def legal():
    return render_template("legal.html")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_id TEXT,
        content TEXT,
        category TEXT,
        severity TEXT,
        score REAL,
        hash TEXT,
        filename TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- AI MODEL ---------------- #

model = Detoxify('original')

def detect_toxicity(text):
    result = model.predict(text)

    score = float(max(result.values()))

    if score >= 0.80:
        severity = "High"
    elif score >= 0.50:
        severity = "Medium"
    else:
        severity = "Low"

    category = max(result, key=result.get)

    return category, severity, round(float(score), 2)

# ---------------- HASH ---------------- #

def generate_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

# ---------------- SAVE DATA ---------------- #

def save_record(evidence_id, content, category, severity, score, hash_val, filename):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO evidence
    (evidence_id, content, category, severity, score, hash, filename, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        evidence_id,
        content,
        category,
        severity,
        score,
        hash_val,
        filename,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

# ---------------- HOME ---------------- #

@app.route("/")
def home():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM evidence")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM evidence WHERE severity='High'")
    high = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM evidence WHERE severity='Medium'")
    medium = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM evidence WHERE severity='Low'")
    low = cur.fetchone()[0]

    conn.close()

    return render_template("index.html",
                           total=total,
                           high=high,
                           medium=medium,
                           low=low)

# ---------------- ANALYZE ---------------- #

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.form["message"]
    file = request.files.get("image")

    filename = ""

    if file and file.filename != "":
        filename = file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    category, severity, score = detect_toxicity(text)

    evidence_id = str(uuid.uuid4())[:8].upper()
    hash_val = generate_hash(text + str(datetime.now()))

    save_record(evidence_id, text, category, severity, float(score), hash_val, filename)

    flash(f"Evidence Stored Successfully | Severity: {severity}")

    return redirect(url_for("vault"))

# ---------------- VAULT ---------------- #

@app.route("/vault")
def vault():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM evidence ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()

    return render_template("vault.html", records=data)

# ---------------- PDF REPORT ---------------- #

@app.route("/report/<evidence_id>")
def report(evidence_id):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,))
    row = cur.fetchone()

    conn.close()

    if not row:
        return "Not Found"

    filename = f"{evidence_id}_report.pdf"

    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(150, 800, "Cyberbullying Legal Evidence Report")

    c.setFont("Helvetica", 12)

    y = 760

    labels = [
        f"Evidence ID: {row[1]}",
        f"Message: {row[2]}",
        f"Category: {row[3]}",
        f"Severity: {row[4]}",
        f"Confidence Score: {row[5]}",
        f"SHA256 Hash: {row[6]}",
        f"Uploaded File: {row[7]}",
        f"Timestamp: {row[8]}"
    ]

    for item in labels:
        c.drawString(50, y, item[:110])
        y -= 30

    c.save()

    return send_file(filename, as_attachment=True)

# ---------------- LEGAL PAGE ---------------- #

@app.route("/legal")
def legal():
    return render_template("legal.html")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)