import mysql.connector
from dotenv import load_dotenv
import os
import csv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# ── PERSONS ──────────────────────────────────────────────

def add_person():
    print("Leave blank if unknown.")
    first = input("First name: ") or "Not Found"
    last = input("Last name: ") or "Not Found"
    email = input("Email: ") or "Not Found"
    phone = input("Phone (###-###-####): ") or "Not Found"
    dob = input("Date of birth (MM-DD-YYYY): ") or None

    conn = get_connection()
    cursor = conn.cursor()

    # Find the next available (gap) ID
    cursor.execute("""
        SELECT MIN(t1.id + 1)
        FROM persons t1
        LEFT JOIN persons t2 ON t2.id = t1.id + 1
        WHERE t2.id IS NULL
    """)
    next_id = cursor.fetchone()[0] or 1

    cursor.execute("""
        INSERT INTO persons (id, first_name, last_name, email, phone, date_of_birth)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (next_id, first, last, email, phone, dob))
    conn.commit()
    conn.close()
    print(f"✅ {first} {last} added with ID #{next_id}!")
    return next_id

def list_all():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name, email, phone FROM persons")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print("No people found.")
        return
    print(f"\n{'ID':<5} {'First':<15} {'Last':<15} {'Email':<25} {'Phone':<15}")
    print("-" * 75)
    for row in rows:
        print(f"{row[0]:<5} {row[1]:<15} {row[2]:<15} {row[3]:<25} {row[4]:<15}")

def search_person():
    term = input("Search by name or email: ")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, first_name, last_name, email, phone FROM persons
        WHERE first_name LIKE %s OR last_name LIKE %s OR email LIKE %s
    """, (f"%{term}%", f"%{term}%", f"%{term}%"))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print("No results found.")
        return
    for row in rows:
        print(f"[{row[0]}] {row[1]} {row[2]} | {row[3]} | {row[4]}")

def update_person():
    list_all()
    pid = input("Enter ID of person to update: ")
    print("Leave blank to keep existing value.")
    first = input("New first name: ")
    last = input("New last name: ")
    email = input("New email: ")
    phone = input("New phone: ")

    conn = get_connection()
    cursor = conn.cursor()
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
    print("✅ Person updated!")

def delete_person():
    list_all()
    pid = input("Enter ID of person to delete: ")
    confirm = input(f"Are you sure you want to delete person #{pid}? (y/n): ")
    if confirm.lower() == 'y':
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM persons WHERE id=%s", (pid,))
        conn.commit()
        conn.close()
        print("✅ Person deleted!")

# ── ADDRESSES ────────────────────────────────────────────

def add_address():
    list_all()
    pid = input("Enter person ID to add address for: ")
    street = input("Street: ")
    city = input("City: ")
    state = input("State: ")
    zip_code = input("ZIP: ")
    country = input("Country: ")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO addresses (person_id, street, city, state, zip, country)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (pid, street, city, state, zip_code, country))
    conn.commit()
    conn.close()
    print("✅ Address added!")

def view_addresses():
    list_all()
    pid = input("Enter person ID to view addresses: ")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT street, city, state, zip, country FROM addresses WHERE person_id=%s
    """, (pid,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print("No addresses found.")
        return
    for row in rows:
        print(f"{row[0]}, {row[1]}, {row[2]} {row[3]}, {row[4]}")

# ── NOTES & TAGS ─────────────────────────────────────────

def add_note():
    list_all()
    pid = input("Enter person ID to add note for: ")
    tag = input("Tag (e.g. work, friend, family): ")
    note = input("Note: ")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notes (person_id, tag, note)
        VALUES (%s, %s, %s)
    """, (pid, tag, note))
    conn.commit()
    conn.close()
    print("✅ Note added!")

def view_notes():
    list_all()
    pid = input("Enter person ID to view notes: ")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tag, note, created_at FROM notes WHERE person_id=%s
    """, (pid,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print("No notes found.")
        return
    for row in rows:
        print(f"[{row[2]}] #{row[0]} — {row[1]}")

# ── EXPORT TO CSV ─────────────────────────────────────────

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

    filename = "export.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "First", "Last", "Email", "Phone", "DOB",
                         "Street", "City", "State", "ZIP", "Country"])
        writer.writerows(rows)
    print(f"✅ Exported to {filename}!")

# ── MENU ──────────────────────────────────────────────────

def main():
    while True:
        print("\n--- Person Database ---")
        print("1.  Add person")
        print("2.  List all")
        print("3.  Search")
        print("4.  Update person")
        print("5.  Delete person")
        print("6.  Add address")
        print("7.  View addresses")
        print("8.  Add note/tag")
        print("9.  View notes")
        print("10. Export to CSV")
        print("11. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":
            add_person()
        elif choice == "2":
            list_all()
        elif choice == "3":
            search_person()
        elif choice == "4":
            update_person()
        elif choice == "5":
            delete_person()
        elif choice == "6":
            add_address()
        elif choice == "7":
            view_addresses()
        elif choice == "8":
            add_note()
        elif choice == "9":
            view_notes()
        elif choice == "10":
            export_csv()
        elif choice == "11":
            print("Goodbye!")
            break
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    main()