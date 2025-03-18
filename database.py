import mysql.connector
import bcrypt

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "090930021",
    "database": "elderly_care"
}

def register_user(username, password, role):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hashed_password, role))

        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return False

def check_user(username, password):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = "SELECT password, role FROM users WHERE username=%s"
        cursor.execute(query, (username,))  # ✅ Pass only one parameter

        user = cursor.fetchone()
        conn.close()
        
        if user and "password" in user:
            if bcrypt.checkpw(password.encode(), user["password"].encode()):
                return user["role"]
        return None
    
    except mysql.connector.Error as e:
        print(f"MySql Error: {e}")
        return None