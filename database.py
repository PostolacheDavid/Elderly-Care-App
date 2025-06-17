import mysql.connector
import bcrypt
from datetime import datetime

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

""" DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "090930021",
    "database": "elderly_care"
} """

DB_CONFIG = {
    "host": "sql7.freesqldatabase.com",
    "user": "sql7784902",
    "password": "Drm7nH6nxU",
    "database": "sql7784902",
    "port": 3306
}

def register_admin(username, password):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Hashing pentru parola
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Inserare in tabelul users
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
    
def add_elder_medication(elder_id, doctor_id, denumire_comerciala, forma_farmaceutica, concentratie, observatii, frecventa):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO elder_medications (elder_id, doctor_id, denumire_comerciala, forma_farmaceutica, concentratie, observatii, frecventa)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (elder_id, doctor_id, denumire_comerciala, forma_farmaceutica, concentratie, observatii, frecventa))

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except mysql.connector.Error as e:
        print(f"MySQL Error (add_elder_medication): {e}")
        return False

def get_medications_for_elder(elder_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT denumire_comerciala, forma_farmaceutica, concentratie, observatii, frecventa
            FROM elder_medications
            WHERE elder_id = %s
        """, (elder_id,))

        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results

    except mysql.connector.Error as e:
        print(f"MySQL Error (get_medications_for_elder): {e}")
        return []

def get_elder_id_for_caregiver(user_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = "SELECT elder_id FROM users WHERE id = %s AND role = 'caregiver'"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        conn.close()
        return result["elder_id"] if result else None
    except mysql.connector.Error as e:
        print(f"MySQL Error (get_elder_id_for_caregiver): {e}")
        return None

def delete_elder_medication(medication_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = "DELETE FROM elder_medications WHERE id = %s"
        cursor.execute(query, (medication_id,))
        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySQL Error (delete_elder_medication): {e}")
        return False

def get_medications_with_id_for_elder(elder_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, denumire_comerciala, forma_farmaceutica, concentratie, frecventa, observatii
            FROM elder_medications
            WHERE elder_id = %s
        """, (elder_id,))

        results = cursor.fetchall()
        conn.close()
        return results

    except mysql.connector.Error as e:
        print(f"MySQL Error (get_medications_with_id_for_elder): {e}")
        return []

def add_medical_control(elder_id, doctor_id, name, goal, details, scheduled_at):
    """
    Insert a row into medical_controls.
      - elder_id, doctor_id: integers
      - name, goal, details: strings
      - scheduled_at: a Python datetime or string 'YYYY-MM-DD HH:MM:SS'
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        #Daca scheduled_at este de tip datetime se converteste la string:
        if isinstance(scheduled_at, datetime):
            scheduled_str = scheduled_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            scheduled_str = scheduled_at

        query = """
            INSERT INTO medical_controls
            (elder_id, doctor_id, name, goal, details, scheduled_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (elder_id, doctor_id, name, goal, details, scheduled_str))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySQL Error (add_medical_control): {e}")
        return False

#Obtinerea listei cu controale ale elder-ului
def get_controls_for_elder(elder_id):
    """
    Return a list of dicts, each representing one control for the given elder_id:
      [
        { "id": 1, "doctor_id": 5, "name": "...", "goal": "...",
          "details": "...", "scheduled_at": "2025-07-01 10:30:00" },
        ...
      ]
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, doctor_id, name, goal, details, scheduled_at
            FROM medical_controls
            WHERE elder_id = %s
            ORDER BY scheduled_at ASC
        """, (elder_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except mysql.connector.Error as e:
        print(f"MySQL Error (get_controls_for_elder): {e}")
        return []

#Stergerea unui control
def delete_medical_control(control_id):
    """
    Deletes the control with the given primary key.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM medical_controls WHERE id = %s", (control_id,))
        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySQL Error (delete_medical_control): {e}")
        return False

def add_elder_document(elder_id, doctor_id, filename, data):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO elder_documents (elder_id, doctor_id, filename, file_data)
            VALUES (%s, %s, %s, %s)
        """, (elder_id, doctor_id, filename, data))
        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"DB Error add_elder_document: {e}")
        return False

def get_documents_for_elder(elder_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, filename, uploaded_at
            FROM elder_documents
            WHERE elder_id = %s
            ORDER BY uploaded_at DESC
        """, (elder_id,))
        docs = cursor.fetchall()
        conn.close()
        return docs
    except mysql.connector.Error as e:
        print(f"DB Error get_documents_for_elder: {e}")
        return []

def get_document_data(doc_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT filename, file_data
            FROM elder_documents
            WHERE id = %s
        """, (doc_id,))
        row = cursor.fetchone()
        conn.close()
        return row if row else None
    except mysql.connector.Error as e:
        print(f"DB Error get_document_data: {e}")
        return None

def delete_elder_document(doc_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM elder_documents WHERE id = %s", (doc_id,))
        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"DB Error delete_elder_document: {e}")
        return False

def add_exercise_for_elder(elder_id: int, title: str, description: str, video_url: str) -> bool:
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO exercises (elder_id, title, description, video_url)
            VALUES (%s, %s, %s, %s)
            """,
            (elder_id, title, description, video_url),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySQL Error (add_exercise_for_elder): {e}")
        return False

def get_exercises_for_elder(elder_id: int) -> list[dict]:
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, title, description, video_url "
        "FROM exercises WHERE elder_id = %s",
        (elder_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
      {"id": r["id"], "title": r["title"], "description": r["description"], "video_url": r["video_url"]}
      for r in rows
    ]

def get_user_email(user_id: int) -> str | None:
    """
    Return the email for the given user_id, or None if not found.
    """
    try:
        conn   = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except mysql.connector.Error as e:
        print(f"MySQL Error (get_user_email): {e}")
        return None

def update_user_profile(user_id: int,
                        new_username: str,
                        new_email: str,
                        new_password: str | None = None
                       ) -> bool:
    """
    Update the given user's username, email, and -- if provided -- password.
    Returns True on success.
    """
    try:
        conn   = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        if new_password:
            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            sql = """
                UPDATE users
                   SET username = %s,
                       email    = %s,
                       password = %s
                 WHERE id       = %s
            """
            params = (new_username, new_email, hashed, user_id)
        else:
            sql = """
                UPDATE users
                   SET username = %s,
                       email    = %s
                 WHERE id       = %s
            """
            params = (new_username, new_email, user_id)

        cursor.execute(sql, params)
        conn.commit()
        conn.close()
        return True

    except mysql.connector.Error as e:
        print(f"MySQL Error (update_user_profile): {e}")
        return False
    
def get_caregivers_by_doctor(doctor_id: int) -> list[dict]:
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
      SELECT id, username
      FROM users
      WHERE role='caregiver' AND doctor_id=%s
    """, (doctor_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def update_linked_user_password(user_id: int, new_password: str) -> bool:
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        cur.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySQL Error (update_linked_user_password): {e}")
        return False
    
def update_linked_user_profile(user_id: int,
                               new_username: str | None = None,
                               new_email:    str | None = None
                              ) -> bool:
    """
    Update only username and/or email for a linked user.
    """
    fields, params = [], []
    if new_username:
        fields.append("username = %s")
        params.append(new_username)
    if new_email:
        fields.append("email = %s")
        params.append(new_email)
    if not fields:
        return True

    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
    params.append(user_id)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur  = conn.cursor()
        cur.execute(sql, tuple(params))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except mysql.connector.Error as e:
        print(f"MySQL Error (update_linked_user_profile): {e}")
        return False

def get_all_users():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, role FROM users ORDER BY username")
        users = cursor.fetchall()
        conn.close()
        return users
    except mysql.connector.Error as e:
        print(f"MySQL Error (get_all_users): {e}")
        return []
