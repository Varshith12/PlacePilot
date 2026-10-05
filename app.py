import os
import sqlite3

from flask import Flask, jsonify, session, send_from_directory
from flask_cors import CORS

from routes.assessment import assessment_bp
from routes.auth import auth_bp, init_db


# --------------------------------------------------
# CREATE FLASK APP
# --------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "development-only-placepilot-secret"
)

CORS(
    app,
    supports_credentials=True
)


# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------

init_db()


# --------------------------------------------------
# REGISTER ROUTES
# --------------------------------------------------

app.register_blueprint(
    assessment_bp,
    url_prefix="/api/assessment"
)

app.register_blueprint(
    auth_bp,
    url_prefix="/api/auth"
)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return send_from_directory(
        app.root_path,
        "index.html"
    )


@app.route("/index.html")
def index():
    return send_from_directory(
        app.root_path,
        "index.html"
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/api/health")
def health():

    return jsonify({
        "status": "healthy",
        "service": "PlacePilot API"
    })


# --------------------------------------------------
# PERSONALIZED DASHBOARD
# --------------------------------------------------

@app.route("/api/dashboard")
def dashboard():

    # Check whether user is logged in
    if "user_id" not in session:

        return jsonify({
            "status": "error",
            "message": "Authentication required"
        }), 401


    user_id = session["user_id"]


    # Get this user's assessment
    conn = sqlite3.connect("placepilot.db")
    conn.row_factory = sqlite3.Row

    assessment = conn.execute("""
        SELECT
            readiness,
            python_score,
            sql_score,
            dsa_score,
            aptitude_score,
            completed_at
        FROM assessments
        WHERE user_id = ?
    """, (user_id,)).fetchone()

    conn.close()


    # --------------------------------------------------
    # NEW USER - NO ASSESSMENT YET
    # --------------------------------------------------

    if assessment is None:

        return jsonify({

            "status": "success",

            "user": {
                "id": user_id,
                "full_name": session["full_name"],
                "email": session["email"]
            },

            "assessment_completed": False,

            "readiness": 0,

            "skill_scores": {
                "Python": 0,
                "SQL": 0,
                "DSA": 0,
                "Aptitude": 0
            },

            "targets": {
                "Python": 75,
                "SQL": 70,
                "DSA": 75,
                "Aptitude": 70
            },

            "gaps": {
                "Python": 75,
                "SQL": 70,
                "DSA": 75,
                "Aptitude": 70
            },

            "priority_skill": "Python",

            "priority_gap": 75,

            "next_best_action": "Take your first assessment"
        })


    # --------------------------------------------------
    # EXISTING USER - ASSESSMENT COMPLETED
    # --------------------------------------------------

    skill_scores = {

        "Python":
            assessment["python_score"],

        "SQL":
            assessment["sql_score"],

        "DSA":
            assessment["dsa_score"],

        "Aptitude":
            assessment["aptitude_score"]
    }


    # Placement targets
    targets = {

        "Python": 75,

        "SQL": 70,

        "DSA": 75,

        "Aptitude": 70
    }


    # Calculate gaps
    gaps = {}

    for skill in targets:

        gaps[skill] = max(
            targets[skill] - skill_scores[skill],
            0
        )


    # Find highest gap
    priority_skill = max(
        gaps,
        key=gaps.get
    )

    priority_gap = gaps[priority_skill]


    # Next Best Action
    actions = {

        "Python":
            "Practice Python fundamentals",

        "SQL":
            "Practice SQL queries and joins",

        "DSA":
            "Start with DSA fundamentals",

        "Aptitude":
            "Practice quantitative aptitude"
    }


    # --------------------------------------------------
    # RETURN PERSONALIZED DATA
    # --------------------------------------------------

    return jsonify({

        "status": "success",

        "user": {

            "id":
                user_id,

            "full_name":
                session["full_name"],

            "email":
                session["email"]
        },

        "assessment_completed":
            True,

        "readiness":
            assessment["readiness"],

        "skill_scores":
            skill_scores,

        "targets":
            targets,

        "gaps":
            gaps,

        "priority_skill":
            priority_skill,

        "priority_gap":
            priority_gap,

        "next_best_action":
            actions[priority_skill],

        "completed_at":
            assessment["completed_at"]
    })


# --------------------------------------------------
# RUN SERVER
# --------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )