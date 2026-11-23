"""ACEest Fitness & Gym - Flask service, release 2.0.0.

Releases: 1.0.0 program catalogue, 2.0.0 client management (calories, BMI),
3.0.0 progress tracking, workout log and membership status.
"""
import os
import socket
import sqlite3

from flask import Flask, g, jsonify, request

VERSION = "2.0.0"

PROGRAMS = {
    "FL": {
        "name": "Fat Loss (FL)",
        "workout": "Mon: 5x5 Back Squat + AMRAP\nTue: EMOM 20min Assault Bike\n"
                   "Wed: Bench Press + 21-15-9\nThu: 10RFT Deadlifts/Box Jumps\n"
                   "Fri: 30min Active Recovery",
        "diet": "B: 3 Egg Whites + Oats Idli\nL: Grilled Chicken + Brown Rice\n"
                "D: Fish Curry + Millet Roti\nTarget: 2,000 kcal",
        "calorie_factor": 22,
    },
    "MG": {
        "name": "Muscle Gain (MG)",
        "workout": "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\n"
                   "Thu: Front Squat 4x8\nFri: Incline Press 4x10\nSat: Barbell Rows 4x10",
        "diet": "B: 4 Eggs + PB Oats\nL: Chicken Biryani (250g Chicken)\n"
                "D: Mutton Curry + Jeera Rice\nTarget: 3,200 kcal",
        "calorie_factor": 35,
    },
    "BG": {
        "name": "Beginner (BG)",
        "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups.\n"
                   "Focus: Technique Mastery & Form (90% Threshold)",
        "diet": "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\nProtein: 120g/day",
        "calorie_factor": 26,
    },
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    age INTEGER, height REAL, weight REAL,
    program TEXT, calories INTEGER,
    membership_status TEXT DEFAULT 'Active',
    membership_end TEXT
);
"""


def calculate_calories(weight, program_code):
    """Daily calorie target = weight (kg) x program factor."""
    if program_code not in PROGRAMS:
        raise ValueError("Unknown program")
    if weight is None or weight <= 0:
        raise ValueError("Weight must be positive")
    return int(weight * PROGRAMS[program_code]["calorie_factor"])


def calculate_bmi(weight_kg, height_cm):
    """Return (bmi, category)."""
    if weight_kg <= 0 or height_cm <= 0:
        raise ValueError("Weight and height must be positive")
    bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return bmi, category


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.environ.get("DB_PATH", "aceest_fitness.db")

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().executescript(SCHEMA)

    def find_client(name):
        return get_db().execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()

    def error(msg, code=400):
        return jsonify({"error": msg}), code

    def info():
        return {"version": VERSION, "hostname": socket.gethostname()}

    @app.get("/")
    def index():
        return jsonify({"service": "ACEest Fitness & Gym", "status": "running", **info()})

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/version")
    def version():
        return jsonify(info())

    @app.get("/programs")
    def list_programs():
        return jsonify({k: v["name"] for k, v in PROGRAMS.items()})

    @app.get("/programs/<code>")
    def get_program(code):
        program = PROGRAMS.get(code.upper())
        if not program:
            return error("Program not found", 404)
        return jsonify(program)

    @app.post("/clients")
    def add_client():
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        if not name:
            return error("Name is required")
        if find_client(name):
            return error("Client already exists", 409)
        program, weight = data.get("program"), data.get("weight")
        calories = None
        if program is not None:
            try:
                calories = calculate_calories(weight, program)
            except (ValueError, TypeError) as exc:
                return error(str(exc))
        db = get_db()
        db.execute(
            "INSERT INTO clients (name, age, height, weight, program, calories,"
            " membership_end) VALUES (?,?,?,?,?,?,?)",
            (name, data.get("age"), data.get("height"), weight, program, calories,
             data.get("membership_end")),
        )
        db.commit()
        return jsonify({"name": name, "calories": calories}), 201

    @app.get("/clients")
    def list_clients():
        rows = get_db().execute("SELECT name, program FROM clients ORDER BY name").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/clients/<name>")
    def get_client(name):
        client = find_client(name)
        if not client:
            return error("Client not found", 404)
        return jsonify(dict(client))

    @app.get("/clients/<name>/bmi")
    def client_bmi(name):
        client = find_client(name)
        if not client:
            return error("Client not found", 404)
        if not client["weight"] or not client["height"]:
            return error("Height and weight required")
        bmi, category = calculate_bmi(client["weight"], client["height"])
        return jsonify({"bmi": bmi, "category": category})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", "5000")))
