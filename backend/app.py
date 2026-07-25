import os

from flask import Flask, jsonify

import models
from database import init_db
from routes.employees import bp as employees_bp
from routes.leave import bp as leave_bp
from routes.payroll import bp as payroll_bp

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")


def create_app(seed_db=True):
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

    init_db(seed=seed_db)

    app.register_blueprint(employees_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(payroll_bp)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/teams")
    def list_teams():
        return jsonify(models.list_teams())

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
