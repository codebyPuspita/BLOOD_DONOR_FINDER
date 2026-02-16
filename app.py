from flask import Flask, request, jsonify, render_template, send_from_directory
import mysql.connector
from models import get_db_connection
from config import SECRET_KEY
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from loguru import logger
import os
import magic
import phonenumbers
from geopy.geocoders import Nominatim
from mysql.connector import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# ----------------------
# LOGGING SETUP
# ----------------------
logger.add("activity.log", rotation="1 MB")

# ----------------------
# FILE UPLOAD CONFIG
# ----------------------
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ----------------------
# HOME ROUTE
# ----------------------
@app.route('/')
def home():
    return "Smart Blood Donor Backend Running"


# ----------------------
# DONOR REGISTRATION
# ----------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    name = data['name']
    email = data['email']
    password = data['password']
    blood_group = data['blood_group']
    location = data['location']
    phone = data.get('phone')

    # Phone validation
    try:
        parsed_number = phonenumbers.parse(phone, "IN")
        if not phonenumbers.is_valid_number(parsed_number):
            return jsonify({"error": "Invalid phone number"}), 400
    except:
        return jsonify({"error": "Invalid phone format"}), 400

    # Convert location to GPS
    geolocator = Nominatim(user_agent="blood_donor_app")
    geo_location = geolocator.geocode(location)

    latitude = geo_location.latitude if geo_location else None
    longitude = geo_location.longitude if geo_location else None

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO donor 
            (name, email, password, blood_group, location, phone, latitude, longitude,
             eligibility_status, availability_status, last_login, role, approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (name, email, hashed_password, blood_group, location, phone,
             latitude, longitude,
             "Eligible", "Active", None, "donor", False)
        )
        conn.commit()

        logger.info(f"New donor registered: {email}")
        return jsonify({"message": "Donor registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


# ----------------------
# DONOR LOGIN + AUTO 90 DAYS CHECK
# ----------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM donor WHERE email = %s", (email,))
    donor = cursor.fetchone()

    if donor and check_password_hash(donor['password'], password):

        # Auto eligibility check (90 days)
        if donor.get("last_donation_date"):
            last_date = donor["last_donation_date"]
            if datetime.now().date() - last_date >= timedelta(days=90):
                cursor.execute(
                    "UPDATE donor SET eligibility_status='Eligible' WHERE id=%s",
                    (donor["id"],)
                )
                conn.commit()

        # Update login time
        cursor.execute(
            "UPDATE donor SET last_login=NOW() WHERE id=%s",
            (donor["id"],)
        )
        conn.commit()

        logger.info(f"Login success: {email}")

        cursor.close()
        conn.close()

        return jsonify({"message": "Login successful"})
    else:
        cursor.close()
        conn.close()
        return jsonify({"error": "Invalid credentials"}), 401


# ----------------------
# SEARCH & FILTER
# ----------------------
@app.route('/search', methods=['POST'])
def search():
    blood_group = request.form['blood_group']
    location = request.form['location']

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT name, blood_group, location, phone 
        FROM donor 
        WHERE blood_group = %s 
        AND location = %s 
        AND availability_status = 'Active'
        AND approved = TRUE
    """
    cursor.execute(query, (blood_group, location))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('search_results.html', results=results)


# ----------------------
# FILE UPLOAD WITH VALIDATION
# ----------------------
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files["file"]

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    file_type = magic.from_file(filepath, mime=True)

    if file_type not in ["image/jpeg", "image/png", "application/pdf"]:
        os.remove(filepath)
        return jsonify({"error": "Invalid file type"}), 400

    return jsonify({"message": "File uploaded successfully"})


# ----------------------
# ADMIN: VIEW ALL DONORS
# ----------------------
@app.route('/admin/donors')
def view_donors():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, blood_group, eligibility_status, availability_status, approved 
        FROM donor
    """)
    donors = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(donors)


# ----------------------
# ADMIN: APPROVE DONOR
# ----------------------
@app.route('/admin/approve/<int:id>')
def approve_donor(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE donor SET approved=TRUE WHERE id=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    logger.info(f"Donor approved: {id}")
    return jsonify({"message": "Donor approved"})


# ----------------------
# ADMIN: DELETE DONOR
# ----------------------
@app.route('/admin/delete/<int:id>')
def delete_donor(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM donor WHERE id=%s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    logger.warning(f"Donor deleted: {id}")
    return jsonify({"message": "Donor deleted"})


# ----------------------
# ADMIN: TOGGLE ACTIVE / INACTIVE
# ----------------------
@app.route('/admin/toggle_availability/<int:id>', methods=['POST'])
def toggle_availability(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT availability_status FROM donor WHERE id=%s", (id,))
    donor = cursor.fetchone()

    if donor:
        new_status = "Inactive" if donor["availability_status"] == "Active" else "Active"

        cursor.execute(
            "UPDATE donor SET availability_status=%s WHERE id=%s",
            (new_status, id)
        )
        conn.commit()

        cursor.close()
        conn.close()

        logger.info(f"Donor {id} availability changed to {new_status}")
        return jsonify({"message": f"Donor status changed to {new_status}"})

    cursor.close()
    conn.close()
    return jsonify({"error": "Donor not found"}), 404


# ----------------------
# GLOBAL ERROR HANDLER
# ----------------------
@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Something went wrong"}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404


# ----------------------
# RUN SERVER
# ----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
