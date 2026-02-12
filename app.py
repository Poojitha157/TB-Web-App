from flask import Flask, render_template, request, send_file
import sqlite3
import random
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer
from reportlab.platypus import ListFlowable
from reportlab.platypus import ListItem
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

DATABASE = "tb_system.db"


# ✅ CREATE DATABASE + TABLE AUTOMATICALLY
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mutations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mutation_code TEXT UNIQUE,
        drug TEXT
    )
    """)

    # Insert basic mutations if empty
    cursor.execute("SELECT COUNT(*) FROM mutations")
    count = cursor.fetchone()[0]

    if count == 0:
        default_mutations = [
            ("S531L", "Rifampicin"),
            ("katG_S315T", "Isoniazid"),
            ("gyrA_D94G", "Fluoroquinolones"),
            ("embB_M306V", "Ethambutol"),
            ("pncA_H57D", "Pyrazinamide")
        ]

        cursor.executemany(
            "INSERT OR IGNORE INTO mutations (mutation_code, drug) VALUES (?, ?)",
            default_mutations
        )

    conn.commit()
    conn.close()


# Run DB init when app starts
init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    mutation = request.form["mutation"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT drug FROM mutations WHERE mutation_code = ?", (mutation,))
    result = cursor.fetchone()
    conn.close()

    if result:
        resistant = result[0]
        classification = "Drug Resistant TB"
        recommended = ["Levofloxacin", "Bedaquiline", "Linezolid"]
    else:
        resistant = None
        classification = "Drug Sensitive TB"
        recommended = ["Isoniazid", "Rifampicin", "Ethambutol", "Pyrazinamide"]

    # Random Doctor
    doctors = [
        {"name": "Dr. Ramesh Kumar", "hospital": "Apollo Hospital", "time": "10:30 AM", "fees": "₹800"},
        {"name": "Dr. Priya Sharma", "hospital": "Global Health City", "time": "12:00 PM", "fees": "₹600"},
        {"name": "Dr. Arjun Mehta", "hospital": "Fortis Hospital", "time": "4:15 PM", "fees": "₹750"}
    ]

    doctor = random.choice(doctors)

    return render_template(
        "index.html",
        resistant=resistant,
        classification=classification,
        recommended=recommended,
        doctor=doctor
    )


if __name__ == "__main__":
    app.run(debug=True)
