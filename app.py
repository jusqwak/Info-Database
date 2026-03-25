from flask import Flask, render_template, request, redirect, url_for, send_file
from dotenv import load_dotenv
import os
import csv
import mysql.connector
import assets

load_dotenv()
app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# ── PERSONS ──────────────────────────────────────────────

@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name, email, phone FROM persons")
    people = cursor.fetchall()
    conn.close()
    return render_template("index.html", people=people)

@app.route("/search")
def search():
    term = request.args.get("q", "")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, first_name, last_name, email, phone FROM persons
        WHERE first_name LIKE %s OR last_name LIKE %s OR email LIKE %s
    """, (f"%{term}%", f"%{term}%", f"%{term}%"))
    people = cursor.fetchall()
    conn.close()
    return render_template("index.html", people=people, search_term=term)

@app.route("/add", methods=["GET", "POST"])
def add_person():
    if request.method == "POST":
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT MIN(t1.id + 1)
            FROM persons t1
            LEFT JOIN persons t2 ON t2.id = t1.id + 1
            WHERE t2.id IS NULL
        """)
        next_id = cursor.fetchone()[0] or 1

        first = request.form.get("first") or "Not Found"
        last = request.form.get("last") or "Not Found"
        email = request.form.get("email") or f"placeholder{next_id}@gmail.com"
        phone = request.form.get("phone") or "Not Found"
        dob = request.form.get("dob") or None

        cursor.execute("""
            INSERT INTO persons (id, first_name, last_name, email, phone, date_of_birth)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (next_id, first, last, email, phone, dob))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add.html")

@app.route("/edit/<int:pid>", methods=["GET", "POST"])
def edit_person(pid):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        first = request.form.get("first")
        last = request.form.get("last")
        email = request.form.get("email")
        phone = request.form.get("phone")
        if first:
            cursor.execute("UPDATE persons SET first_name=%s WHERE id=%s", (first, pid))
        if last:
            cursor.execute("UPDATE persons SET last_name=%s WHERE id=%s", (last, pid))
        if email:
            cursor.execute("UPDATE persons SET email=%s WHERE id=%s", (email, pid))
        if phone:
            cursor.execute("UPDATE persons SET phone=%s WHERE id=%s", (phone, pid))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    cursor.execute("SELECT id, first_name, last_name, email, phone FROM persons WHERE id=%s", (pid,))
    person = cursor.fetchone()
    conn.close()
    return render_template("edit.html", person=person)

@app.route("/delete/<int:pid>", methods=["POST"])
def delete_person(pid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM persons WHERE id=%s", (pid,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# ── PERSON DETAIL (addresses + notes) ────────────────────

@app.route("/person/<int:pid>")
def person_detail(pid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, first_name, last_name, email, phone, date_of_birth FROM persons WHERE id=%s", (pid,))
    person = cursor.fetchone()

    cursor.execute("SELECT id, street, city, state, zip, country FROM addresses WHERE person_id=%s", (pid,))
    addresses = cursor.fetchall()

    cursor.execute("SELECT id, tag, note, created_at FROM notes WHERE person_id=%s ORDER BY created_at DESC", (pid,))
    notes = cursor.fetchall()

    conn.close()
    return render_template("person.html", person=person, addresses=addresses, notes=notes)

# ── ADDRESSES ────────────────────────────────────────────

@app.route("/person/<int:pid>/add_address", methods=["POST"])
def add_address(pid):
    street = request.form.get("street")
    city = request.form.get("city")
    state = request.form.get("state")
    zip_code = request.form.get("zip")
    country = request.form.get("country")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO addresses (person_id, street, city, state, zip, country)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (pid, street, city, state, zip_code, country))
    conn.commit()
    conn.close()
    return redirect(url_for("person_detail", pid=pid))

@app.route("/address/delete/<int:aid>/<int:pid>", methods=["POST"])
def delete_address(aid, pid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM addresses WHERE id=%s", (aid,))
    conn.commit()
    conn.close()
    return redirect(url_for("person_detail", pid=pid))

# ── NOTES ────────────────────────────────────────────────

@app.route("/person/<int:pid>/add_note", methods=["POST"])
def add_note(pid):
    tag = request.form.get("tag")
    note = request.form.get("note")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notes (person_id, tag, note)
        VALUES (%s, %s, %s)
    """, (pid, tag, note))
    conn.commit()
    conn.close()
    return redirect(url_for("person_detail", pid=pid))

@app.route("/note/delete/<int:nid>/<int:pid>", methods=["POST"])
def delete_note(nid, pid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id=%s", (nid,))
    conn.commit()
    conn.close()
    return redirect(url_for("person_detail", pid=pid))

# ── EXPORT CSV ───────────────────────────────────────────

@app.route("/export")
def export_csv():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.first_name, p.last_name, p.email, p.phone, p.date_of_birth,
               a.street, a.city, a.state, a.zip, a.country
        FROM persons p
        LEFT JOIN addresses a ON p.id = a.person_id
    """)
    rows = cursor.fetchall()
    conn.close()

    filename = "/tmp/export.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "First", "Last", "Email", "Phone", "DOB",
                         "Street", "City", "State", "ZIP", "Country"])
        writer.writerows(rows)
    return send_file(filename, as_attachment=True, download_name="export.csv")

if __name__ == "__main__":
    app.run(debug=True)