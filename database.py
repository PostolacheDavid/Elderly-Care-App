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

def register_admin(username, password):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insert into users table
        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hashed_password, "admin"))

        conn.commit()
        cursor.close()
        conn.close()
        print("Admin registered successfully.")
        return True
    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return False

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

        query = "SELECT id, password, role FROM users WHERE username=%s"
        cursor.execute(query, (username,))

        user = cursor.fetchone()
        conn.close()
        
        if user and "password" in user:
            if bcrypt.checkpw(password.encode(), user["password"].encode()):
                return user["role"], user["id"]
        return None

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return None

    
def submit_doctor_request(full_name, email, password, photo_data):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        query = """
        INSERT INTO pending_doctors (full_name, email, password, photo)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (full_name, email, hashed_password, photo_data))

        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySql Error: {e}")
        return False
    except Exception as ex:
        print(f"General Error: {ex}")
        return False
    
def get_pending_doctors():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, full_name, email, photo FROM pending_doctors")
        results = cursor.fetchall()

        conn.close()
        return results
    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return []

def approve_doctor(doctor_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, email, password, photo FROM pending_doctors where id = %s", (doctor_id,))
        doctor = cursor.fetchone()

        if doctor:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (doctor[0], doctor[2], "doctor")
            )
            cursor.execute("DELETE FROM pending_doctors WHERE id = %s", (doctor_id,))
            conn.commit()

        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySql Errir: {e}")
        return False
    
def create_linked_user(full_name, email, password, role, doctor_id, elder_id=None):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        if role == "caregiver":
            query = """
                INSERT INTO users (username, password, role, doctor_id, elder_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (email, hashed_password, role, doctor_id, elder_id))
        else:
            query = """
                INSERT INTO users (username, password, role, doctor_id)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (email, hashed_password, role, doctor_id))

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return False

def get_elders_by_doctor(doctor_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, username
        FROM users
        WHERE role = 'elder' AND doctor_id = %s
        """
        cursor.execute(query, (doctor_id,))
        elders = cursor.fetchall()

        conn.close()
        return elders

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
        return []


