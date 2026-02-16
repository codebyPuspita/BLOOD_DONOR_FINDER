from models import get_db_connection
from werkzeug.security import generate_password_hash

def test_insert():
    conn = get_db_connection()
    if conn is None:
        print("❌ Failed to connect to Database. Check your config.py password!")
        return
    
    cursor = conn.cursor()
    try:
        # Creating a test donor
        hashed_pw = generate_password_hash("test123")
        cursor.execute(
            "INSERT INTO donor (name, email, password, blood_group) VALUES (%s, %s, %s, %s)",
            ("Test User", "test@example.com", hashed_pw, "O+")
        )
        conn.commit()
        print("✅ Success! Database is working and donor was saved.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_insert()
    
