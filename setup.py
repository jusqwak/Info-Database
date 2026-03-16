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

conn.commit()
conn.close()