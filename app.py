from flask import Flask, render_template, request, redirect, send_file
import sqlite3, datetime, csv, random
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_bcrypt import Bcrypt
from reportlab.pdfgen import canvas
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ML
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

app = Flask(__name__)
app.secret_key = "secret123"

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# -------- USER --------
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect('tb_system.db')
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        result TEXT,
        date TEXT)''')

    conn.commit()
    conn.close()

init_db()

# -------- ML TRAINING --------
def train_model():
    df = pd.read_csv("tb_mutations.csv")

    genes = ["rpoB","katG","inhA","gyrA","rrs","embB","pncA"]

    X = []
    y = []

    for _, row in df.iterrows():
        features = [1 if row["gene"] == g else 0 for g in genes]
        X.append(features)

        if row["gene"] in ["rpoB","katG","inhA"]:
            y.append(1)
        elif row["gene"] in ["gyrA","rrs"]:
            y.append(2)
        else:
            y.append(0)

    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    model = RandomForestClassifier(n_estimators=200)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    return model, acc, genes

model, accuracy, genes_list = train_model()

# -------- PREDICTION --------
def predict_tb(m):
    m = m.lower()

    features = [1 if g.lower() in m else 0 for g in genes_list]
    pred = model.predict([features])[0]

    if pred == 1:
        return "MDR-TB"
    elif pred == 2:
        return "XDR-TB"
    return "Drug Sensitive TB"

# -------- DRUG SYSTEM --------
def recommend_drug(m):
    m = m.lower()

    if "rpob" in m:
        return "Rifampicin resistance → Bedaquiline + Linezolid"
    elif "katg" in m:
        return "High-level INH resistance → Levofloxacin regimen"
    elif "inha" in m:
        return "Low-level INH resistance → Adjusted HR regimen"
    elif "gyra" in m:
        return "Fluoroquinolone resistance → XDR protocol"
    elif "rrs" in m:
        return "Injectable resistance → Advanced MDR/XDR therapy"
    elif "embb" in m:
        return "Ethambutol resistance → Alternative regimen"
    elif "pnca" in m:
        return "Pyrazinamide resistance → Modified MDR regimen"

    return "Standard TB therapy (HRZE)"

# -------- DOCTOR --------
doctors = [
    {"name": "Dr. Rajesh Sharma", "hospital": "AIIMS Delhi", "city": "Delhi", "cost": "₹800-1500", "time": "10:00 AM"},
    {"name": "Dr. Priya Nair", "hospital": "Apollo Hospitals", "city": "Chennai", "cost": "₹700-1200", "time": "2:00 PM"},
    {"name": "Dr. Amit Verma", "hospital": "Fortis Hospital", "city": "Mumbai", "cost": "₹900-1600", "time": "4:30 PM"},
    {"name": "Dr. Sneha Reddy", "hospital": "Yashoda Hospital", "city": "Hyderabad", "cost": "₹600-1000", "time": "11:30 AM"},
    {"name": "Dr. Karthik Iyer", "hospital": "CMC Vellore", "city": "Vellore", "cost": "₹500-900", "time": "1:00 PM"},
]

def get_doctor():
    return random.choice(doctors)

# -------- CHART --------
def generate_chart():
    conn = sqlite3.connect('tb_system.db')
    cur = conn.cursor()

    cur.execute("SELECT result FROM reports")
    data = cur.fetchall()
    conn.close()

    mdr = sum(1 for r in data if "MDR" in r[0])
    xdr = sum(1 for r in data if "XDR" in r[0])
    normal = len(data) - mdr - xdr

    plt.figure()
    plt.bar(['MDR','XDR','Normal'], [mdr,xdr,normal])
    plt.title("TB Resistance Distribution")
    plt.savefig('static/chart.png')
    plt.close()

# -------- ROUTES --------
@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        conn = sqlite3.connect('tb_system.db')
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users VALUES (NULL,?,?)",(u,p))
            conn.commit()
        except:
            return "User exists"

        conn.close()
        return redirect('/login')

    return render_template("register.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect('tb_system.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (u,))
        user = cur.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], p):
            login_user(User(user[0]))
            return redirect('/dashboard')

        return "Invalid login"

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        name = request.form['name']
        mut = request.form.get('mutation','')

        if 'file' in request.files:
            f = request.files['file']
            if f.filename != '':
                mut = f.read().decode('utf-8')

        tb = predict_tb(mut)
        drug = recommend_drug(mut)
        result = tb + " detected"

        doctor = get_doctor()

        conn = sqlite3.connect('tb_system.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO reports VALUES (NULL,?,?,?)",
                    (name,result,str(datetime.datetime.now())))
        conn.commit()
        conn.close()

        pdf = f"report_{name}.pdf"
        c = canvas.Canvas(pdf)
        c.drawString(100,800,"TB REPORT")
        c.drawString(100,780,f"Patient: {name}")
        c.drawString(100,760,f"Prediction: {tb}")
        c.drawString(100,740,f"Drug: {drug}")
        c.drawString(100,720,f"Model Accuracy: {round(accuracy*100,2)}%")
        c.save()

        return render_template("dashboard.html",
                               result=result,
                               drug=drug,
                               tb_type=tb,
                               pdf=pdf,
                               doctor=doctor,
                               accuracy=round(accuracy*100,2))

    return render_template("dashboard.html",
                           accuracy=round(accuracy*100,2))

@app.route('/download/<f>')
@login_required
def download(f):
    return send_file(f, as_attachment=True)

@app.route('/stats')
@login_required
def stats():
    generate_chart()
    return render_template("stats.html")

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)