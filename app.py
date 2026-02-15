from flask import Flask, request, jsonify
import mysql.connector
from models import get_db_connection
from config import SECRET_KEY
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


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

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO donor (name, email, password, blood_group, location, eligibility_status, availability_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (name, email, hashed_password, blood_group, location, "Eligible", "Active")
        )
        conn.commit()
        return jsonify({"message": "Donor registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


# ----------------------
# DONOR LOGIN
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

    cursor.close()
    conn.close()

    if donor and check_password_hash(donor['password'], password):
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# @app.route('/add_donor', methods=['POST'])
# def add_donor():
#     data = request.get_json()
#     name = data.get('name')
#     blood_group = data.get('blood_group')
#     email = data.get('email')
#     phone = data.get('phone')
#     city = data.get('city')

#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute(
#         "INSERT INTO donors (name, blood_group, email, phone, city) VALUES (%s, %s, %s, %s, %s)",
#         (name, blood_group, email, phone, city)
#     )
#     conn.commit()
#     cursor.close()
#     conn.close()
#     return jsonify({"message": "Donor added successfully!"})


# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

