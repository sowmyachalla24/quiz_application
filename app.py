import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM quizzes")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO quizzes
                (question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            ("What is the unit of resistance?", "Ohm", "Volt", "Ampere", "Watt", "a"),
            ("What is the unit of current?", "Ohm", "Volt", "Ampere", "Watt", "c"),
            ("What is the unit of voltage?", "Ohm", "Volt", "Ampere", "Watt", "b"),
            ("What is the unit of power?", "Ohm", "Volt", "Ampere", "Watt", "d"),
            ("What is the unit of energy?", "Ohm", "Joule", "Ampere", "Watt", "b"),
        ])

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
    correct_answers = session.get("correct_answers", 0)
    total_questions = session.get("total_questions", 5)
    return render_template(
        "results.html",
        score=session.get("score", f"{correct_answers}/{total_questions}"),
        correct_answers=correct_answers,
        total_questions=total_questions,
    )

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
    conn = get_db_connection()
    quizzes = conn.execute("SELECT * FROM quizzes ORDER BY id").fetchall()
    conn.close()
    return render_template("quiz.html", quizzes=quizzes)

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
        (name, email, generate_password_hash(password), dob, str(gender).strip(), "")
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

    answer_map = {
        answer.get("question"): answer.get("answer")
        for answer in user_answers
        if isinstance(answer, dict)
    }
    conn = get_db_connection()
    quizzes = conn.execute("SELECT * FROM quizzes ORDER BY id").fetchall()
    score = sum(
        answer_map.get(f"q{quiz['id']}") == quiz["correct_option"]
        for quiz in quizzes
    )
    total_questions = len(quizzes)
    session["correct_answers"] = score
    session["total_questions"] = total_questions
    session["score"] = f"{score}/{total_questions}"
    
    recommended_courses = 'Electrical Engineering, Computer Science'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET courses = ? WHERE id = ?', 
        (recommended_courses, user_id)
    )
    cursor.execute(
        "INSERT INTO results (user_id, score, total_questions) VALUES (?, ?, ?)",
        (user_id, score, total_questions)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'message': 'Quiz submitted successfully!', 
        'courses': [c.strip() for c in recommended_courses.split(",")],
        'score': f"{score}/{total_questions}"
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

@app.route('/api/quizzes', methods=['POST'])
def create_quiz():
    # If you want to require login:
    # if 'user_id' not in session:
    #     return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()

    question = data.get('question')
    option_a = data.get('option_a')
    option_b = data.get('option_b')
    option_c = data.get('option_c')
    option_d = data.get('option_d')
    correct_option = data.get('correct_option')

    # Save to SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO quizzes (question, option_a, option_b, option_c, option_d, correct_option)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (question, option_a, option_b, option_c, option_d, correct_option))
    
    conn.commit()
    conn.close()

    # Return success response
    return jsonify({"message": "quiz submitted successfully"}), 201


if __name__ == "__main__":
    init_db() 
    app.run(debug=True)

