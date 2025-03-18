import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "090930021",
    "database": "elderly_care"
}

def check_user(username, password):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = "SELECT role FROM users WHERE username=%s AND password=%s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        conn.close()
        return user["role"] if user else None
    except mysql.connector.Error as e:
        print(f"MySql Error: {e}")
        return None