import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key"

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT NOT NULL,
            courses TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

# HTML Pages Routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/results")
def results():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("results.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/quiz")
def quiz():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("quiz.html")

# Authentication APIs
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing request body"}), 400

    email = data.get("email")
    name = data.get("name")
    password = data.get("password")
    dob = data.get("dob")
    gender = data.get("gender")

    if not all([email, name, password, dob, gender]):
        return jsonify({"message": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"message": "Email already registered"}), 400

    cursor.execute(
        "INSERT INTO users (name, email, password, dob, gender, courses) VALUES (?, ?, ?, ?, ?, ?)",
        (name, email, hashed_password, dob, str(gender).strip(), "")
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing request body"}), 400

    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        return jsonify({"message": "Login successful"}), 200
    
    return jsonify({"message": "Invalid email or password"}), 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/api/quiz', methods=['POST'])
def api_quiz():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
        
    data = request.get_json()
    if not data or 'answers' not in data:
        return jsonify({'message': 'Answers are required'}), 400
        
    user_answers = data.get('answers')
    user_id = session['user_id']
    
    recommended_courses = 'Electrical Engineering, Computer Science'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET courses = ? WHERE id = ?', 
        (recommended_courses, user_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'Quiz submitted successfully!', 
        'courses': [c.strip() for c in recommended_courses.split(",")]
    }), 200

@app.route("/api/results", methods=["GET"])
def api_results():
    if "user_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT courses FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        courses_list = [c.strip() for c in user["courses"].split(",")] if user["courses"] else []
        return jsonify({"courses": courses_list}), 200
    
    return jsonify({"message": "User not found"}), 404

if __name__ == "__main__":
    init_db() 
    app.run(debug=True)

