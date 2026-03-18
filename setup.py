import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS people_db")
cursor.execute("USE people_db")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS persons (
        id            INT PRIMARY KEY AUTO_INCREMENT,
        first_name    VARCHAR(50)  NOT NULL,
        last_name     VARCHAR(50)  NOT NULL,
        email         VARCHAR(100) UNIQUE,
        phone         VARCHAR(20),
        date_of_birth DATE,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("Database and table created successfully!")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS addresses (
        id          INT PRIMARY KEY AUTO_INCREMENT,
        person_id   INT NOT NULL,
        street      VARCHAR(100),
        city        VARCHAR(50),
        state       VARCHAR(50),
        zip         VARCHAR(10),
        country     VARCHAR(50),
        FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id          INT PRIMARY KEY AUTO_INCREMENT,
        person_id   INT NOT NULL,
        tag         VARCHAR(50),
        note        TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
    )
""")

print("All tables created successfully!")

conn.commit()
conn.close()