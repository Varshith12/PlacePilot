import sqlite3

from flask import Blueprint, jsonify, request, session


assessment_bp = Blueprint("assessment", __name__)

DB_PATH = "placepilot.db"


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_assessment_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            readiness INTEGER NOT NULL,
            python_score INTEGER DEFAULT 0,
            sql_score INTEGER DEFAULT 0,
            dsa_score INTEGER DEFAULT 0,
            aptitude_score INTEGER DEFAULT 0,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# Create table when Flask starts
init_assessment_db()


# --------------------------------------------------
# ASSESSMENT QUESTIONS
# --------------------------------------------------

QUESTIONS = [
    {
        "id": 1,
        "skill": "DSA",
        "topic": "Data Structures",
        "question": "Which data structure follows FIFO?",
        "options": [
            "Stack",
            "Queue",
            "Tree",
            "Graph"
        ],
        "answer": "Queue"
    },

    {
        "id": 2,
        "skill": "Python",
        "topic": "Python Basics",
        "question": "Which keyword is used to define a function in Python?",
        "options": [
            "func",
            "define",
            "def",
            "function"
        ],
        "answer": "def"
    },

    {
        "id": 3,
        "skill": "SQL",
        "topic": "SQL Basics",
        "question": "Which SQL command is used to retrieve data?",
        "options": [
            "GET",
            "SELECT",
            "FETCH",
            "OPEN"
        ],
        "answer": "SELECT"
    },

    {
        "id": 4,
        "skill": "Aptitude",
        "topic": "Percentages",
        "question": "What is 20% of 200?",
        "options": [
            "20",
            "30",
            "40",
            "50"
        ],
        "answer": "40"
    },

    {
        "id": 5,
        "skill": "DSA",
        "topic": "Algorithms",
        "question": "Which algorithm is commonly used to find the shortest path in a weighted graph?",
        "options": [
            "Binary Search",
            "Dijkstra's Algorithm",
            "Bubble Sort",
            "DFS"
        ],
        "answer": "Dijkstra's Algorithm"
    }
]


# --------------------------------------------------
# GET QUESTIONS
# --------------------------------------------------

@assessment_bp.route("/questions", methods=["GET"])
def get_questions():

    questions_without_answers = []

    for question in QUESTIONS:

        questions_without_answers.append({
            "id": question["id"],
            "skill": question["skill"],
            "topic": question["topic"],
            "question": question["question"],
            "options": question["options"]
        })

    return jsonify({
        "status": "success",
        "total_questions": len(questions_without_answers),
        "questions": questions_without_answers
    })


# --------------------------------------------------
# SUBMIT ASSESSMENT
# --------------------------------------------------

@assessment_bp.route("/submit", methods=["POST"])
def submit_assessment():

    # ----------------------------------------------
    # Check login
    # ----------------------------------------------

    if "user_id" not in session:

        return jsonify({
            "status": "error",
            "message": "Authentication required. Please login first."
        }), 401


    # ----------------------------------------------
    # Read request
    # ----------------------------------------------

    data = request.get_json()

    if not data or "answers" not in data:

        return jsonify({
            "status": "error",
            "message": "Answers are required"
        }), 400


    answers = data["answers"]


    # ----------------------------------------------
    # Score structure
    # ----------------------------------------------

    scores = {

        "Python": {
            "correct": 0,
            "total": 0
        },

        "SQL": {
            "correct": 0,
            "total": 0
        },

        "DSA": {
            "correct": 0,
            "total": 0
        },

        "Aptitude": {
            "correct": 0,
            "total": 0
        }
    }


    # ----------------------------------------------
    # Calculate scores
    # ----------------------------------------------

    for question in QUESTIONS:

        skill = question["skill"]

        if skill not in scores:
            continue

        scores[skill]["total"] += 1

        submitted_answer = answers.get(
            str(question["id"])
        )

        if submitted_answer == question["answer"]:

            scores[skill]["correct"] += 1


    # ----------------------------------------------
    # Convert to percentages
    # ----------------------------------------------

    skill_scores = {}

    for skill, result in scores.items():

        if result["total"] > 0:

            skill_scores[skill] = round(
                (
                    result["correct"]
                    / result["total"]
                ) * 100
            )

        else:

            skill_scores[skill] = 0


    # ----------------------------------------------
    # Overall readiness
    # ----------------------------------------------

    readiness = round(
        sum(skill_scores.values())
        / len(skill_scores)
    )


    # ----------------------------------------------
    # Current logged-in user
    # ----------------------------------------------

    user_id = session["user_id"]


    # ----------------------------------------------
    # Save assessment for THIS user
    # ----------------------------------------------

    conn = get_db()

    conn.execute("""
        INSERT INTO assessments (
            user_id,
            readiness,
            python_score,
            sql_score,
            dsa_score,
            aptitude_score
        )

        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )

        ON CONFLICT(user_id)
        DO UPDATE SET

            readiness = excluded.readiness,

            python_score = excluded.python_score,

            sql_score = excluded.sql_score,

            dsa_score = excluded.dsa_score,

            aptitude_score = excluded.aptitude_score,

            completed_at = CURRENT_TIMESTAMP

    """, (

        user_id,

        readiness,

        skill_scores["Python"],

        skill_scores["SQL"],

        skill_scores["DSA"],

        skill_scores["Aptitude"]

    ))


    conn.commit()
    conn.close()


    # ----------------------------------------------
    # Response
    # ----------------------------------------------

    return jsonify({

        "status": "success",

        "message": "Assessment saved successfully",

        "user_id": user_id,

        "readiness": readiness,

        "skill_scores": skill_scores

    })