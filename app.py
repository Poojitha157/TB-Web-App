from flask import Flask, render_template, request, send_from_directory
import sqlite3
import os
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

DATABASE = "tb_system.db"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- ANALYZE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    mutation = request.form["mutation"].strip()

    # Connect to SQLite database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT drug FROM mutations WHERE mutation_code = ?", (mutation,))
    result = cursor.fetchone()
    conn.close()

    resistant = None
    classification = "Drug Sensitive TB"
    recommended = ["Isoniazid", "Rifampicin", "Ethambutol", "Pyrazinamide"]

    if result:
        resistant = result[0]

        if resistant in ["Rifampicin", "Isoniazid"]:
            classification = "MDR-TB"
            recommended = ["Levofloxacin", "Bedaquiline", "Linezolid"]
        elif resistant == "Fluoroquinolones":
            classification = "XDR-TB"
            recommended = ["Bedaquiline", "Linezolid", "Clofazimine"]
        else:
            classification = "Drug Resistant TB"
            recommended = ["Consult Specialist"]

    # ---------------- Generate PDF ----------------
    pdf_file = f"{name}_TB_Report.pdf"
    pdf_path = os.path.join(os.getcwd(), pdf_file)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(50, 750, "TB Drug Resistance Report")
    c.drawString(50, 720, f"Patient Name: {name}")
    c.drawString(50, 700, f"Age: {age}")
    c.drawString(50, 680, f"Gender: {gender}")
    c.drawString(50, 660, f"Mutation: {mutation}")
    c.drawString(50, 640, f"Resistance Detected: {resistant}")
    c.drawString(50, 620, f"Classification: {classification}")

    y = 600
    c.drawString(50, y, "Recommended Regimen:")
    for drug in recommended:
        y -= 20
        c.drawString(70, y, f"- {drug}")

    c.save()

    # ---------------- Random Doctor Recommendation ----------------
    doctors = [
        {"name": "Dr. Arjun Rao", "hospital": "Apollo Hospital", "time": "10:30 AM", "fees": "₹800"},
        {"name": "Dr. Meera Nair", "hospital": "Fortis Hospital", "time": "2:00 PM", "fees": "₹700"},
        {"name": "Dr. Kiran Patel", "hospital": "AIIMS", "time": "11:45 AM", "fees": "₹500"},
        {"name": "Dr. Sneha Sharma", "hospital": "Global Health City", "time": "4:15 PM", "fees": "₹900"}
    ]

    doctor = random.choice(doctors)

    return render_template("index.html",
                           resistant=resistant,
                           classification=classification,
                           recommended=recommended,
                           pdf_file=pdf_file,
                           doctor=doctor)


# ---------------- DOWNLOAD PDF ----------------
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(os.getcwd(), filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
