from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "tb_secret_key"

DATABASE = "tb_system.db"


# ---------------- LOGIN ---------------- #

@app.route("/")
def home():
    if "user" in session:
        return render_template("index.html")
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "1234":
        session["user"] = username
        return redirect(url_for("home"))
    else:
        return "Invalid Login"


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


# ---------------- ANALYZE ---------------- #

@app.route("/analyze", methods=["POST"])
def analyze():

    name = request.form["name"]
    age = request.form["age"]
    gender = request.form["gender"]
    mutation = request.form["mutation"]
    doctor = request.form["doctor"]

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT drug FROM mutations WHERE mutation_code=?", (mutation,))
    result = cursor.fetchone()

    if result:
        resistant = result[0]
        classification = "Drug Resistant TB"

        recommended = [
            "Levofloxacin",
            "Bedaquiline",
            "Linezolid"
        ]
    else:
        resistant = "None"
        classification = "Drug Sensitive TB"

        recommended = [
            "Isoniazid",
            "Rifampicin",
            "Ethambutol",
            "Pyrazinamide"
        ]

    conn.close()

    # -------- PDF GENERATION -------- #

    pdf_file = f"{name}_TB_Report.pdf"
    pdf_path = os.path.join("reports", pdf_file)

    if not os.path.exists("reports"):
        os.makedirs("reports")

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, f"Patient Name: {name}")
    c.drawString(100, 730, f"Age: {age}")
    c.drawString(100, 710, f"Gender: {gender}")
    c.drawString(100, 690, f"Mutation: {mutation}")
    c.drawString(100, 670, f"Resistance: {resistant}")
    c.drawString(100, 650, f"Classification: {classification}")
    c.drawString(100, 630, f"Recommended by: Dr. {doctor}")
    c.drawString(100, 610, "Recommended Drugs:")

    y = 590
    for drug in recommended:
        c.drawString(120, y, drug)
        y -= 20

    c.save()

    return render_template(
        "index.html",
        resistant=resistant,
        classification=classification,
        recommended=recommended,
        doctor=doctor,
        pdf_file=pdf_file
    )


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("reports", filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
