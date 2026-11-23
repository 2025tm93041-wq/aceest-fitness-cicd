"""ACEest Fitness & Gym - Flask service, release 1.0.0.

Releases: 1.0.0 program catalogue, 2.0.0 client management (calories, BMI),
3.0.0 progress tracking, workout log and membership status.
"""
import os
import socket

from flask import Flask, jsonify

VERSION = "1.0.0"

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


def create_app(db_path=None):
    app = Flask(__name__)

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

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", "5000")))
