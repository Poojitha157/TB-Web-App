from flask import Flask, render_template, request
import sqlite3
import random

app = Flask(__name__)

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    conn = sqlite3.connect("tb_system.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------- HOME PAGE ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- ANALYZE ROUTE ----------
@app.route("/analyze", methods=["POST"])
def analyze():

    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    mutation = request.form["mutation"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT drug FROM mutation WHERE code = ?", (mutation,))
    result = cursor.fetchone()
    conn.close()

    if result:
        resistant = result["drug"]

        # Classification Logic
        if resistant in ["Isoniazid", "Rifampicin"]:
            classification = "MDR-TB"
            recommended = ["Levofloxacin", "Bedaquiline", "Linezolid"]
        elif resistant in ["Fluoroquinolones"]:
            classification = "XDR-TB"
            recommended = ["Bedaquiline", "Delamanid", "Linezolid"]
        else:
            classification = "Drug Resistant TB"
            recommended = ["Specialist Evaluation Required"]

    else:
        resistant = "None"
        classification = "Drug Sensitive TB"
        recommended = ["Isoniazid", "Rifampicin", "Ethambutol", "Pyrazinamide"]

    # -------- RANDOM DOCTOR ASSIGNMENT --------
    doctors = [
        {"name": "Dr. Priya Sharma", "hospital": "Apollo Hospital", "fees": 800},
        {"name": "Dr. Arjun Reddy", "hospital": "Global Hospitals", "fees": 700},
        {"name": "Dr. Meera Nair", "hospital": "Fortis Hospital", "fees": 900},
        {"name": "Dr. Rahul Verma", "hospital": "AIIMS", "fees": 500},
        {"name": "Dr. Kavya Iyer", "hospital": "Care Hospitals", "fees": 750}
    ]

    selected_doctor = random.choice(doctors)
    appointment_time = "Tomorrow 10:30 AM"

    return render_template(
        "index.html",
        resistant=resistant,
        classification=classification,
        recommended=recommended,
        doctor=selected_doctor,
        appointment_time=appointment_time
    )


if __name__ == "__main__":
    app.run(debug=True)
