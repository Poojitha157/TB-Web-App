from flask import Flask, render_template, request, send_file
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
import os

app = Flask(__name__)

# ===== Initialize SQLite Database =====
def init_db():
    conn = sqlite3.connect("tb_system.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            gender TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mutation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mutation_code TEXT,
            resistant_drug TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drug (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug_name TEXT,
            category TEXT
        )
    """)

    # Insert default mutation data if empty
    cursor.execute("SELECT COUNT(*) FROM mutation")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO mutation (mutation_code, resistant_drug) VALUES (?, ?)",
            [
                ("S531L", "Rifampicin"),
                ("S315T", "Isoniazid"),
                ("D94G", "Fluoroquinolones")
            ]
        )

    # Insert default drug data if empty
    cursor.execute("SELECT COUNT(*) FROM drug")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO drug (drug_name, category) VALUES (?, ?)",
            [
                ("Isoniazid", "First Line"),
                ("Rifampicin", "First Line"),
                ("Ethambutol", "First Line"),
                ("Pyrazinamide", "First Line"),
                ("Levofloxacin", "Second Line"),
                ("Bedaquiline", "Second Line"),
                ("Linezolid", "Second Line")
            ]
        )

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    mutation_code = request.form["mutation"]

    conn = sqlite3.connect("tb_system.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO patient (name, age, gender) VALUES (?, ?, ?)",
        (name, age, gender)
    )

    cursor.execute(
        "SELECT resistant_drug FROM mutation WHERE mutation_code=?",
        (mutation_code,)
    )

    result = cursor.fetchone()

    if result:
        resistant_drug = result[0]

        if resistant_drug in ["Rifampicin", "Isoniazid"]:
            classification = "MDR-TB"
        elif resistant_drug in ["Fluoroquinolones"]:
            classification = "XDR-TB"
        else:
            classification = "Drug Resistant TB"

        cursor.execute("SELECT drug_name FROM drug WHERE category='Second Line'")
        recommended = [row[0] for row in cursor.fetchall()]
    else:
        resistant_drug = "None"
        classification = "Drug Sensitive TB"

        cursor.execute("SELECT drug_name FROM drug WHERE category='First Line'")
        recommended = [row[0] for row in cursor.fetchall()]

    conn.commit()
    conn.close()

    # ===== Generate PDF =====
    file_name = f"{name}_TB_Report.pdf"
    file_path = os.path.join(os.getcwd(), file_name)

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("TB Drug Resistance Report", styles["Title"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Name: {name}", styles["Normal"]))
    elements.append(Paragraph(f"Age: {age}", styles["Normal"]))
    elements.append(Paragraph(f"Gender: {gender}", styles["Normal"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Mutation: {mutation_code}", styles["Normal"]))
    elements.append(Paragraph(f"Resistance: {resistant_drug}", styles["Normal"]))
    elements.append(Paragraph(f"Classification: {classification}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    drug_list = [ListItem(Paragraph(drug, styles["Normal"])) for drug in recommended]
    elements.append(ListFlowable(drug_list))

    doc.build(elements)

    return render_template(
        "index.html",
        name=name,
        age=age,
        gender=gender,
        resistant=resistant_drug,
        classification=classification,
        recommended=recommended,
        pdf_file=file_name
    )

@app.route("/download/<filename>")
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
