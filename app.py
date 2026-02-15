from flask import Flask, request, jsonify
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


if __name__ == '__main__':
    app.run(debug=True)
